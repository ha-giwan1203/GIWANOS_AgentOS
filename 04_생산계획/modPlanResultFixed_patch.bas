' =========================================================
' [PATCH] GetModelGroup 동적 조회 개선
' 기존 하드코딩 40개 차종 코드 → 기준 정보 B열에서 동적 수집
' GPT 합의 조건 9개 반영
' =========================================================

' --- 모듈 레벨 변수 (기존 상수 선언부 아래에 추가) ---
Private mModelKeys() As String    ' 길이 내림차순 정렬된 모델 코드 배열
Private mModelKeysCount As Long   ' 유효 코드 수

' =========================================================
' BuildModelKeys: B열 차종에서 모델 코드 동적 수집
' 조건: B열만 원천, P/R 제외
' 추출: 선두 영숫자 토큰 + UCase 정규화
' 정렬: 길이 내림차순 (긴 코드 우선 매칭)
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

    ' B열(차종)에서 고유 모델 코드 수집
    For r = 2 To lastRow
        raw = Trim$(CStr(wsInfo.Cells(r, "B").Value))
        If Len(raw) > 0 Then
            code = ExtractLeadingAlphaNum(raw)
            If Len(code) >= 2 Then
                If Not tmpDict.Exists(code) Then
                    tmpDict(code) = True
                End If
            End If
        End If
    Next r

    ' Dictionary → 배열로 변환
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

    ' 길이 내림차순 정렬 (Bubble Sort - 코드 수 ~40개이므로 충분)
    For i = 1 To cnt - 1
        For j = i + 1 To cnt
            If arrLen(j) > arrLen(i) Then
                tmpStr = arr(i): arr(i) = arr(j): arr(j) = tmpStr
                tmpLen = arrLen(i): arrLen(i) = arrLen(j): arrLen(j) = tmpLen
            ElseIf arrLen(j) = arrLen(i) Then
                ' 같은 길이면 알파벳순
                If arr(j) < arr(i) Then
                    tmpStr = arr(i): arr(i) = arr(j): arr(j) = tmpStr
                End If
            End If
        Next j
    Next i

    ' 모듈 레벨 배열에 저장
    ReDim mModelKeys(1 To cnt)
    For i = 1 To cnt
        mModelKeys(i) = arr(i)
    Next i
    mModelKeysCount = cnt
End Sub

' =========================================================
' ExtractLeadingAlphaNum: 선두 영숫자 토큰 추출 + UCase
' "RG3 EV (G80)" → "RG3"
' "SP3(180도)" → "SP3"
' "BC4T(90도)" → "BC4T"
' "JXO (PLL)" → "JXO"
' "NX5a" → "NX5A"
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
            ' 영숫자가 아닌 첫 문자에서 중단 (공백, (, 도 등)
            If Len(result) > 0 Then Exit For
        End If
    Next i

    ExtractLeadingAlphaNum = result
End Function

' =========================================================
' GetModelGroup 수정본: Dictionary 기반 동적 매칭
' 변경: txtAll 대신 CarType 단일값만 받음
' 매칭: 길이 내림차순 정렬 배열 순차 비교
' =========================================================
Private Function GetModelGroup(ByVal carTypeText As String) As String
    Dim u As String
    Dim i As Long

    If mModelKeysCount = 0 Then
        GetModelGroup = "UNKNOWN_MODEL"
        Exit Function
    End If

    u = UCase$(Trim$(carTypeText))

    If Len(u) = 0 Then
        GetModelGroup = "UNKNOWN_MODEL"
        Exit Function
    End If

    ' 길이 내림차순으로 매칭 (긴 코드 우선)
    For i = 1 To mModelKeysCount
        If InStr(1, u, mModelKeys(i), vbTextCompare) > 0 Then
            GetModelGroup = mModelKeys(i)
            Exit Function
        End If
    Next i

    GetModelGroup = "UNKNOWN_MODEL"
End Function

' =========================================================
' BuildInfoMap 수정: BuildModelKeys 호출 추가
' 캐시 초기화 포함 (GPT 조건 #9)
' =========================================================
' 기존 BuildInfoMap 의 첫 줄에 아래 2줄 추가:
'   mModelKeysCount = 0
'   BuildModelKeys wsInfo
'
' 즉:
' Private Sub BuildInfoMap(ByVal wsInfo As Worksheet, ByRef dictInfo As Object)
'     mModelKeysCount = 0          ' ← 추가: 캐시 초기화
'     BuildModelKeys wsInfo        ' ← 추가: 모델 코드 동적 수집
'     ... (기존 코드 유지)

' =========================================================
' BuildItem 수정: GetModelGroup 호출 변경
' 기존: item("ModelGroup") = GetModelGroup(txtAll)
' 수정: item("ModelGroup") = GetModelGroup(item("CarType"))
' =========================================================
