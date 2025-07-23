#!/usr/bin/env python
import os
import json
from typing import List

def chunk_by_sentences(text: str, chunk_size: int) -> List[str]:
    sentences = text.split(". ")
    chunks = []
    current = []
    for sentence in sentences:
        current.append(sentence)
        if len(current) >= chunk_size:
            chunks.append(". ".join(current))
            current = []
    if current:
        chunks.append(". ".join(current))
    return chunks

def chunk_by_time(logs: List[dict], window_minutes: int) -> List[List[dict]]:
    chunks = []
    current_chunk = []
    last_time = None
    for log in logs:
        if last_time is None:
            last_time = log['timestamp']
        time_diff = log['timestamp'] - last_time
        if time_diff > window_minutes * 60:
            chunks.append(current_chunk)
            current_chunk = []
        current_chunk.append(log)
        last_time = log['timestamp']
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def run_test():
    dummy_text = "오늘은 날씨가 좋아. 회의를 잘 마쳤고, 팀 분위기가 괜찮았어. 내일은 기획안을 다시 검토할 예정이야. 그 외엔 큰 이슈는 없었어."
    result = chunk_by_sentences(dummy_text, 2)
    print("✅ 문장 기준 청크 결과:")
    for i, c in enumerate(result):
        print(f"Chunk {i+1}: {c}\n")

if __name__ == "__main__":
    run_test()
