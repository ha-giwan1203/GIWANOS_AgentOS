#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { appendFileSync, mkdirSync } from 'fs'
import { dirname, resolve } from 'path'

const PORT = Number(process.env.CODEX_BRIDGE_PORT ?? 8791)
const WORKSPACE = resolve(process.env.CODEX_WORKSPACE ?? process.cwd())
const listeners = new Set<(chunk: string) => void>()
let channelReady = false

function sendSse(event: Record<string, unknown>) {
  const data = `data: ${JSON.stringify(event)}\n\n`
  for (const emit of listeners) emit(data)
}

function safeReviewPath(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) return null
  const target = resolve(WORKSPACE, value)
  const allowedRoot = resolve(WORKSPACE, '90_공통기준', '업무관리', '검토기록', 'runs')
  if (target !== allowedRoot && !target.startsWith(`${allowedRoot}\\`)) return null
  return target
}

function appendReview(path: string, text: string) {
  mkdirSync(dirname(path), { recursive: true })
  appendFileSync(path, `\n${text.trim()}\n`, { encoding: 'utf8' })
}

const mcp = new Server(
  { name: 'codex-bridge', version: '0.0.1' },
  {
    capabilities: { tools: {}, experimental: { 'claude/channel': {} } },
    instructions:
      'Codex review requests arrive as <channel source="codex-bridge" request_id="..." review_path="...">. ' +
      'Review the referenced local request and current git diff. Reply only by calling the reply tool with request_id, text, and review_path. ' +
      'The text must include verdict, reason, commit approval, and any follow-up.',
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: 'Record Claude review result for a Codex bridge request.',
      inputSchema: {
        type: 'object',
        properties: {
          request_id: { type: 'string' },
          text: { type: 'string' },
          review_path: { type: 'string' },
        },
        required: ['request_id', 'text'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  if (req.params.name !== 'reply') {
    return { content: [{ type: 'text', text: `unknown tool: ${req.params.name}` }], isError: true }
  }
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  const requestId = String(args.request_id ?? '')
  const text = String(args.text ?? '').trim()
  const reviewPath = safeReviewPath(args.review_path)
  const entry = `## ${new Date().toISOString()} - Claude channel reply\n\n- request_id: \`${requestId}\`\n\n\`\`\`text\n${text}\n\`\`\`\n`
  if (reviewPath) appendReview(reviewPath, entry)
  sendSse({ type: 'reply', request_id: requestId, text, review_path: reviewPath })
  return { content: [{ type: 'text', text: reviewPath ? 'recorded' : 'sent' }] }
})

let seq = 0
function nextId() {
  return `codex-${Date.now()}-${++seq}`
}

Bun.serve({
  port: PORT,
  hostname: '127.0.0.1',
  idleTimeout: 0,
  async fetch(req) {
    const url = new URL(req.url)
    if (req.method === 'GET' && url.pathname === '/health') {
      return Response.json({ ok: true, channel_ready: channelReady, name: 'codex-bridge', port: PORT })
    }
    if (req.method === 'GET' && url.pathname === '/events') {
      const stream = new ReadableStream({
        start(ctrl) {
          ctrl.enqueue(': connected\n\n')
          const emit = (chunk: string) => ctrl.enqueue(chunk)
          listeners.add(emit)
          req.signal.addEventListener('abort', () => listeners.delete(emit))
        },
      })
      return new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
      })
    }
    if (req.method === 'POST' && url.pathname === '/request') {
      const payload = await req.json().catch(() => null) as null | {
        request_id?: string
        content?: string
        review_path?: string
      }
      if (!payload?.content) return new Response('missing content', { status: 400 })
      if (!channelReady) return new Response('channel not ready', { status: 503 })
      const requestId = payload.request_id || nextId()
      const meta: Record<string, string> = {
        request_id: requestId,
        kind: 'codex_review',
        ts: new Date().toISOString(),
      }
      if (payload.review_path) meta.review_path = payload.review_path
      await mcp.notification({
        method: 'notifications/claude/channel',
        params: { content: payload.content, meta },
      })
      return Response.json({ ok: true, request_id: requestId })
    }
    return new Response('not found', { status: 404 })
  },
})

process.stderr.write(`codex-bridge: http://127.0.0.1:${PORT}\n`)

await mcp.connect(new StdioServerTransport())
channelReady = true
process.stderr.write('codex-bridge: channel ready\n')
