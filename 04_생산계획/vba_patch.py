import oletools.olevba as olevba

# Extract full modPlanResultFixed code
vba_parser = olevba.VBA_Parser("SP3M3_생산지시서_메크로자동화_v2.xlsm")
original_code = None
for (filename, stream_path, vba_filename, vba_code) in vba_parser.extract_macros():
    if vba_filename == "modPlanResultFixed.bas":
        original_code = vba_code
        break
vba_parser.close()

lines = original_code.split("\n")

# === Mod 1: Add module-level variables ===
last_const_idx = 0
for i, line in enumerate(lines):
    if "Private Const COL_PLAN_STORE_KEY" in line:
        last_const_idx = i
        break

new_vars = [
    "",
    "' [PATCH] dynamic model code array",
    "Private mModelKeys() As String",
    "Private mModelKeysCount As Long",
]
for idx, nv in enumerate(new_vars):
    lines.insert(last_const_idx + 1 + idx, nv)

# === Mod 2: BuildItem - change GetModelGroup call ===
for i, line in enumerate(lines):
    if "GetModelGroup(txtAll)" in line:
        lines[i] = line.replace("GetModelGroup(txtAll)", 'GetModelGroup(item("CarType"))')
        print(f"Mod2: BuildItem call changed at line {i+1}")
        break

# === Mod 3: BuildInfoMap - add initialization ===
for i, line in enumerate(lines):
    if "Private Sub BuildInfoMap(ByVal wsInfo As Worksheet, ByRef dictInfo As Object)" in line:
        init_lines = [
            "    mModelKeysCount = 0",
            "    BuildModelKeys wsInfo",
            "",
        ]
        for idx, il in enumerate(init_lines):
            lines.insert(i + 1 + idx, il)
        print(f"Mod3: Added init in BuildInfoMap at line {i+1}")
        break

# === Mod 4: Replace GetModelGroup ===
gm_start = None
gm_end = None
for i, line in enumerate(lines):
    if "Private Function GetModelGroup(ByVal txtAll As String) As String" in line:
        gm_start = i
    if gm_start is not None and i > gm_start:
        if line.strip() == "End Function":
            gm_end = i
            break

new_gm = [
    "Private Function GetModelGroup(ByVal carTypeText As String) As String",
    "    Dim key As String",
    "    Dim i As Long",
    "",
    "    If mModelKeysCount = 0 Then",
    '        GetModelGroup = "UNKNOWN_MODEL"',
    "        Exit Function",
    "    End If",
    "",
    "    key = ExtractLeadingAlphaNum(carTypeText)",
    "",
    "    If Len(key) = 0 Then",
    '        GetModelGroup = "UNKNOWN_MODEL"',
    "        Exit Function",
    "    End If",
    "",
    "    For i = 1 To mModelKeysCount",
    "        If StrComp(key, mModelKeys(i), vbTextCompare) = 0 Then",
    "            GetModelGroup = mModelKeys(i)",
    "            Exit Function",
    "        End If",
    "    Next i",
    "",
    '    GetModelGroup = "UNKNOWN_MODEL"',
    "End Function",
]

if gm_start is not None and gm_end is not None:
    print(f"Mod4: Replacing GetModelGroup lines {gm_start+1}-{gm_end+1}")
    lines[gm_start:gm_end+1] = new_gm

# === Mod 5: Add new functions before GetModelGroup ===
for i, line in enumerate(lines):
    if "Private Function GetModelGroup(ByVal carTypeText As String) As String" in line:
        new_gm_pos = i
        break

new_funcs = """' =========================================================
' BuildModelKeys: B col dynamic model code collection
' =========================================================
Private Sub BuildModelKeys(ByVal wsInfo As Worksheet)
    Dim lastRow As Long
    Dim r As Long
    Dim raw As String
    Dim code As String
    Dim tmpDict As Object
    Dim k As Variant
    Dim arr() As String
    Dim arrLen() As Long
    Dim cnt As Long
    Dim i As Long
    Dim j As Long
    Dim tmpStr As String
    Dim tmpLen As Long

    Set tmpDict = CreateObject("Scripting.Dictionary")
    lastRow = wsInfo.Cells(wsInfo.Rows.Count, "A").End(xlUp).Row

    For r = 2 To lastRow
        raw = Trim$(CStr(wsInfo.Cells(r, "B").Value))
        If Len(raw) > 0 Then
            code = ExtractLeadingAlphaNum(raw)
            If Len(code) > 0 Then
                If Not tmpDict.Exists(code) Then
                    tmpDict(code) = True
                End If
            End If
        End If
    Next r

    cnt = tmpDict.Count
    If cnt = 0 Then
        mModelKeysCount = 0
        Exit Sub
    End If

    ReDim arr(1 To cnt)
    ReDim arrLen(1 To cnt)
    i = 1
    For Each k In tmpDict.Keys
        arr(i) = CStr(k)
        arrLen(i) = Len(arr(i))
        i = i + 1
    Next k

    For i = 1 To cnt - 1
        For j = i + 1 To cnt
            If arrLen(j) > arrLen(i) Then
                tmpStr = arr(i): arr(i) = arr(j): arr(j) = tmpStr
                tmpLen = arrLen(i): arrLen(i) = arrLen(j): arrLen(j) = tmpLen
            ElseIf arrLen(j) = arrLen(i) Then
                If arr(j) < arr(i) Then
                    tmpStr = arr(i): arr(i) = arr(j): arr(j) = tmpStr
                End If
            End If
        Next j
    Next i

    ReDim mModelKeys(1 To cnt)
    For i = 1 To cnt
        mModelKeys(i) = arr(i)
    Next i
    mModelKeysCount = cnt
End Sub

' =========================================================
' ExtractLeadingAlphaNum: leading alphanum token + UCase
' =========================================================
Private Function ExtractLeadingAlphaNum(ByVal raw As String) As String
    Dim s As String
    Dim i As Long
    Dim ch As String
    Dim result As String

    s = UCase$(Trim$(raw))
    result = ""

    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If (ch >= "A" And ch <= "Z") Or (ch >= "0" And ch <= "9") Then
            result = result & ch
        Else
            If Len(result) > 0 Then Exit For
        End If
    Next i

    ExtractLeadingAlphaNum = result
End Function

""".split("\n")

for idx, nf in enumerate(new_funcs):
    lines.insert(new_gm_pos + idx, nf)

# Write modified code
modified_code = "\n".join(lines)
with open("modPlanResultFixed_modified.bas", "w", encoding="utf-8") as f:
    f.write(modified_code)

print(f"\nResult: {len(modified_code)} bytes (orig {len(original_code)} bytes)")

# Verify
for i, line in enumerate(lines):
    if 'GetModelGroup(item("CarType"))' in line:
        print(f"OK: BuildItem call at line {i+1}")
    if "BuildModelKeys wsInfo" in line and "Sub BuildInfoMap" not in line and "Sub BuildModelKeys" not in line:
        print(f"OK: BuildModelKeys in BuildInfoMap at line {i+1}")
    if "Private Function GetModelGroup(ByVal carTypeText" in line:
        print(f"OK: GetModelGroup signature at line {i+1}")
    if "Private Sub BuildModelKeys" in line:
        print(f"OK: BuildModelKeys function at line {i+1}")
    if "Private Function ExtractLeadingAlphaNum" in line:
        print(f"OK: ExtractLeadingAlphaNum at line {i+1}")
