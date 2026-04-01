Attribute VB_Name = "modPlanResultFixed"
Option Private Module
Option Explicit

Private Const SHEET_INFO As String = "SP3 LINE 기준 정보"
Private Const SHEET_PLAN As String = "생산계획"
Private Const SHEET_CHECK As String = "계획 확인"
Private Const SHEET_RESULT As String = "PLAN_RESULT_FIXED"
Private Const SHEET_BACKUP As String = "PLAN_BACKUP_FIXED"

Private Const NIGHT_LIMIT_QTY As Double = 3900

Private Const NIGHT_DATA_START As Long = 3
Private Const NIGHT_DATA_END As Long = 100
Private Const NIGHT_TOTAL_ROW As Long = 101

Private Const DAY_TITLE_ROW As Long = 102
Private Const DAY_HEADER_ROW As Long = 103
Private Const DAY_DATA_START As Long = 104
Private Const DAY_DATA_END As Long = 203
Private Const DAY_TOTAL_ROW_1 As Long = 204
Private Const DAY_TOTAL_ROW_2 As Long = 205
Private Const DAY_TOTAL_ROW_3 As Long = 206

Private Const COL_PLAN_SEQ As Long = 2        ' B
Private Const COL_PLAN_SUB As Long = 5        ' E
Private Const COL_PLAN_TIME As Long = 7       ' G
Private Const COL_PLAN_CARRY As Long = 20     ' T
Private Const COL_PLAN_MANUAL_SEC As Long = 22 ' V : 저장 구간(야간/주간)
Private Const COL_PLAN_MANUAL_SEQ As Long = 23 ' W : 저장 순번
Private Const COL_PLAN_STORE_KEY As Long = 24 ' X : 고유 식별키

' [PATCH] dynamic model code array
Private mModelKeys() As String
Private mModelKeysCount As Long

' =========================================================
' 메인
' =========================================================
Public Sub PreviewBuildCore()
    Dim wb As Workbook
    Dim wsInfo As Worksheet
    Dim wsCheck As Worksheet
    Dim wsRes As Worksheet
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean

    On Error GoTo EH

    Set wb = ThisWorkbook
    Set wsInfo = wb.Worksheets(SHEET_INFO)
    Set wsCheck = wb.Worksheets(SHEET_CHECK)
    Set wsRes = GetOrCreateSheet(wb, SHEET_RESULT)

    SaveAppState oldCalc, oldScreen, oldEvents
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    RecalcCheckSheet wsCheck
    BuildResultSheet wsCheck, wsInfo, wsRes

SAFE_EXIT:
    RestoreAppState oldCalc, oldScreen, oldEvents
    Exit Sub

EH:
    MsgBox "PREVIEW_BUILD 오류: " & Err.Description, vbExclamation
    Resume SAFE_EXIT
End Sub

Public Sub ApplyToPlanCore()
    Dim wb As Workbook
    Dim wsInfo As Worksheet
    Dim wsCheck As Worksheet
    Dim wsRes As Worksheet
    Dim wsPlan As Worksheet
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim storedMap As Object
    Dim restoredCount As Long

    On Error GoTo EH

    Set wb = ThisWorkbook
    Set wsInfo = wb.Worksheets(SHEET_INFO)
    Set wsCheck = wb.Worksheets(SHEET_CHECK)
    Set wsRes = GetOrCreateSheet(wb, SHEET_RESULT)
    Set wsPlan = wb.Worksheets(SHEET_PLAN)

    Set storedMap = CreateObject("Scripting.Dictionary")
    SnapshotStoredOrder wsPlan, storedMap

    SaveAppState oldCalc, oldScreen, oldEvents
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    RecalcCheckSheet wsCheck
    BackupPlanSheet wb
    BuildResultSheet wsCheck, wsInfo, wsRes
    ApplyResultToPlan wsRes, wsPlan
    RestoreStoredOrderFromSnapshot wsPlan, storedMap, restoredCount
    WritePlanTotals wsPlan
    HideBlankPlanRows wsPlan
    wsPlan.Calculate
    modPlanMoveSnapshot.ClearMoveSnapshot

    If restoredCount > 0 Then
        MsgBox "생산계획 반영 완료 / 저장서열 복원 " & restoredCount & "건", vbInformation
    Else
        MsgBox "생산계획 반영 완료", vbInformation
    End If

SAFE_EXIT:
    RestoreAppState oldCalc, oldScreen, oldEvents
    Exit Sub

EH:
    MsgBox "APPLY_TO_PLAN 오류: " & Err.Description, vbExclamation
    Resume SAFE_EXIT
End Sub

Public Sub RestorePlanCore()
    Dim wb As Workbook
    Dim wsPlan As Worksheet
    Dim wsBak As Worksheet
    Dim rngCopy As Range
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean

    On Error GoTo EH

    Set wb = ThisWorkbook
    Set wsPlan = wb.Worksheets(SHEET_PLAN)

    On Error Resume Next
    Set wsBak = wb.Worksheets(SHEET_BACKUP)
    On Error GoTo EH

    If wsBak Is Nothing Then
        MsgBox "백업 시트를 찾을 수 없습니다.", vbExclamation
        Exit Sub
    End If

    SaveAppState oldCalc, oldScreen, oldEvents
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    Set rngCopy = GetPlanBackupRange(wsBak)
    wsPlan.Range(rngCopy.Address).Clear
    rngCopy.Copy
    wsPlan.Range(rngCopy.Address).PasteSpecial xlPasteAll
    Application.CutCopyMode = False

    wsPlan.Calculate
    modPlanMoveSnapshot.ClearMoveSnapshot

    MsgBox "생산계획 복원 완료", vbInformation

SAFE_EXIT:
    RestoreAppState oldCalc, oldScreen, oldEvents
    Exit Sub

EH:
    MsgBox "RESTORE_PLAN 오류: " & Err.Description, vbExclamation
    Resume SAFE_EXIT
End Sub

' =========================================================
' 계산 재실행
' =========================================================
Private Sub RecalcCheckSheet(ByVal wsCheck As Worksheet)
    wsCheck.Calculate
    DoEvents
End Sub

' =========================================================
' 결과 빌드
' D+1 = 야간 원천
' NIGHT = D+1 정렬 후 3900 컷
' DAY = 먼저 NIGHT 이월분, 그 다음 D+2 정렬 결과
' =========================================================
Private Sub BuildResultSheet(ByVal wsCheck As Worksheet, ByVal wsInfo As Worksheet, ByVal wsRes As Worksheet)
    Dim infoMap As Object
    Dim d1Raw As Collection
    Dim d2Raw As Collection
    Dim d1Sorted As Collection
    Dim nightFinal As Collection
    Dim carryToDay As Collection
    Dim d2Sorted As Collection
    Dim dayFinal As Collection

    Set infoMap = CreateObject("Scripting.Dictionary")
    BuildInfoMap wsInfo, infoMap

    Set d1Raw = LoadNightItems(wsCheck, infoMap)
    Set d1Sorted = SortItemsByUserCriteria(d1Raw)

    Set carryToDay = New Collection
    Set nightFinal = ApplyNightCut(d1Sorted, carryToDay)

    Set d2Raw = LoadDayItems(wsCheck, infoMap)
    Set d2Sorted = SortItemsByUserCriteria(d2Raw)

    Set dayFinal = New Collection
    AppendCollection dayFinal, ConvertCarryToDay(carryToDay)
    AppendCollection dayFinal, d2Sorted

    WriteResultSheet wsRes, nightFinal, dayFinal
End Sub

' =========================================================
' D+1 / D+2 읽기
' =========================================================
Private Function LoadNightItems(ByVal wsCheck As Worksheet, ByVal infoMap As Object) As Collection
    Dim col As New Collection
    Dim r As Long
    Dim subPart As String
    Dim needQty As Double
    Dim orderQty As Double
    Dim tmText As String
    Dim seqNo As Long

    seqNo = 0

    For r = 4 To 250
        subPart = Trim$(CStr(wsCheck.Cells(r, "C").Value))

        If Len(subPart) > 0 Then
            needQty = NzD(wsCheck.Cells(r, "F").Value)
            orderQty = NzD(wsCheck.Cells(r, "G").Value)
            If orderQty <= 0 Then orderQty = needQty

            If orderQty > 0 Then
                seqNo = seqNo + 1
                tmText = Trim$(CStr(wsCheck.Cells(r, "D").Text))
                If Len(tmText) = 0 Then tmText = "12:00"
                col.Add BuildItem("NIGHT", subPart, tmText, orderQty, infoMap, seqNo)
            End If
        End If
    Next r

    Set LoadNightItems = col
End Function

Private Function LoadDayItems(ByVal wsCheck As Worksheet, ByVal infoMap As Object) As Collection
    Dim col As New Collection
    Dim r As Long
    Dim subPart As String
    Dim qty As Double
    Dim seqNo As Long

    seqNo = 0

    For r = 4 To 250
        subPart = Trim$(CStr(wsCheck.Cells(r, "L").Value))

        If Len(subPart) > 0 Then
            qty = NzD(wsCheck.Cells(r, "M").Value)

            If qty > 0 Then
                seqNo = seqNo + 1
                col.Add BuildItem("DAY", subPart, "12:00", qty, infoMap, seqNo)
            End If
        End If
    Next r

    Set LoadDayItems = col
End Function

' =========================================================
' Item 생성
' =========================================================
Private Function BuildItem(ByVal shiftType As String, ByVal subPart As String, ByVal timeText As String, ByVal qty As Double, ByVal infoMap As Object, ByVal seqNo As Long) As Object
    Dim item As Object
    Dim arrInfo As Variant
    Dim txtAll As String
    Dim pTrayType As String
    Dim angleType As String
    Dim actualModel As String

    Set item = CreateObject("Scripting.Dictionary")
    arrInfo = GetInfoArray(infoMap, subPart)

    item("ShiftType") = shiftType
    item("OriginType") = shiftType
    item("SubPart") = subPart
    item("TimeText") = timeText
    item("Qty") = qty
    item("SourceSeq") = seqNo
    item("PlanKey") = BuildPlanKey(shiftType, subPart, seqNo)

    item("CarType") = NzS(arrInfo(0))
    item("PartNo") = NzS(arrInfo(1))
    item("ModulePart") = NzS(arrInfo(2))
    item("SenseSpec") = NzS(arrInfo(3))
    item("SenseLoc") = NzS(arrInfo(4))
    item("Housing") = NzS(arrInfo(5))
    item("Holder") = NzS(arrInfo(6))
    item("TorsionText") = NzS(arrInfo(7))
    item("TorsionLoc") = NzS(arrInfo(8))
    item("FrameLoc") = NzS(arrInfo(9))
    item("NoteText") = NzS(arrInfo(10))

    pTrayType = UCase$(Trim$(NzS(arrInfo(11))))
    angleType = UCase$(Trim$(NzS(arrInfo(12))))

    txtAll = UCase$(item("CarType") & " " & item("PartNo") & " " & item("ModulePart") & " " & item("SenseSpec") & " " & item("NoteText") & " " & item("TorsionText"))

    item("PiType") = GetPiType(txtAll)
    item("IsPLL") = IsPLLText(txtAll)
    item("TorsionNum") = GetTorsionNumber(item("TorsionText"))
    item("ModelGroup") = GetModelGroup(item("CarType"))
    item("CarFamily") = GetCarFamily(item("CarType"))

    actualModel = Trim$(NzS(arrInfo(13)))
    If Len(actualModel) = 0 Then actualModel = Trim$(NzS(arrInfo(14)))
    If Len(actualModel) = 0 Then actualModel = item("ModelGroup")
    item("ActualModel") = UCase$(actualModel)

    item("PTrayFlag") = IsPTrayType( _
        pTrayType, _
        item("CarType"), _
        item("PartNo"), _
        item("ModulePart"), _
        item("NoteText") _
    )

    item("AngleKey") = NormalizeAngleKey(angleType, CBool(item("PTrayFlag")))
    item("DirectionKey") = GetDirectionKey(item("CarType") & " " & item("NoteText"))
    item("CarryFlag") = False

    Set BuildItem = item
End Function

Private Function BuildPlanKey(ByVal originType As String, ByVal subPart As String, ByVal seqNo As Long) As String
    BuildPlanKey = UCase$(Trim$(originType)) & "|" & Trim$(subPart) & "|" & Format$(seqNo, "00000")
End Function

' =========================================================
' 사용자 기준 정렬
' 823 = 10PI 바로 뒤
' =========================================================
Private Function SortItemsByUserCriteria(ByVal items As Collection) As Collection
    Dim arr() As Object
    Dim i As Long
    Dim outCol As New Collection

    If items.Count = 0 Then
        Set SortItemsByUserCriteria = outCol
        Exit Function
    End If

    ReDim arr(1 To items.Count)
    For i = 1 To items.Count
        Set arr(i) = items(i)
    Next i

    QuickSortItems arr, LBound(arr), UBound(arr)

    For i = LBound(arr) To UBound(arr)
        outCol.Add arr(i)
    Next i

    Set SortItemsByUserCriteria = outCol
End Function

Private Sub QuickSortItems(ByRef arr() As Object, ByVal firstIdx As Long, ByVal lastIdx As Long)
    Dim i As Long
    Dim j As Long
    Dim pivot As Object
    Dim tmp As Object

    i = firstIdx
    j = lastIdx
    Set pivot = arr((firstIdx + lastIdx) \ 2)

    Do While i <= j
        Do While CompareItemsByUserCriteria(arr(i), pivot) < 0
            i = i + 1
        Loop
        Do While CompareItemsByUserCriteria(arr(j), pivot) > 0
            j = j - 1
        Loop

        If i <= j Then
            Set tmp = arr(i)
            Set arr(i) = arr(j)
            Set arr(j) = tmp
            i = i + 1
            j = j - 1
        End If
    Loop

    If firstIdx < j Then QuickSortItems arr, firstIdx, j
    If i < lastIdx Then QuickSortItems arr, i, lastIdx
End Sub

Private Function CompareItemsByUserCriteria(ByVal a As Object, ByVal b As Object) As Long
    Dim v1 As Variant
    Dim v2 As Variant

    v1 = GetPiRankByUserRule(NzS(a("PiType")), NzS(a("SubPart")))
    v2 = GetPiRankByUserRule(NzS(b("PiType")), NzS(b("SubPart")))
    CompareItemsByUserCriteria = CompareVariant(v1, v2)
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    v1 = GetTorsionRankByUserRule(NzS(a("PiType")), NzD(a("TorsionNum")))
    v2 = GetTorsionRankByUserRule(NzS(b("PiType")), NzD(b("TorsionNum")))
    CompareItemsByUserCriteria = CompareVariant(v1, v2)
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    v1 = GetPTrayInnerRank(NzD(a("TorsionNum")), CBool(a("PTrayFlag")), NzS(a("PiType")))
    v2 = GetPTrayInnerRank(NzD(b("TorsionNum")), CBool(b("PTrayFlag")), NzS(b("PiType")))
    CompareItemsByUserCriteria = CompareVariant(v1, v2)
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    If CBool(a("PTrayFlag")) Or CBool(b("PTrayFlag")) Then
        v1 = GetAngleRankValue(NzS(a("AngleKey")))
        v2 = GetAngleRankValue(NzS(b("AngleKey")))
        CompareItemsByUserCriteria = CompareVariant(v1, v2)
        If CompareItemsByUserCriteria <> 0 Then Exit Function
    End If

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("ActualModel")), CleanKey(b("ActualModel")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("CarFamily")), CleanKey(b("CarFamily")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("Housing")), CleanKey(b("Housing")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("Holder")), CleanKey(b("Holder")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("SenseSpec")), CleanKey(b("SenseSpec")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(CleanKey(a("NoteText")), CleanKey(b("NoteText")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareSubPart(CStr(a("SubPart")), CStr(b("SubPart")))
    If CompareItemsByUserCriteria <> 0 Then Exit Function

    CompareItemsByUserCriteria = CompareVariant(NzD(a("SourceSeq")), NzD(b("SourceSeq")))
End Function

' =========================================================
' NIGHT 3900 컷
' =========================================================
Private Function ApplyNightCut(ByVal nightOrdered As Collection, ByRef carryToDay As Collection) As Collection
    Dim outCol As New Collection
    Dim i As Long
    Dim item As Object
    Dim cumQty As Double
    Dim overLocked As Boolean

    cumQty = 0
    overLocked = False

    For i = 1 To nightOrdered.Count
        Set item = nightOrdered(i)

        If Not overLocked Then
            outCol.Add item
            cumQty = cumQty + NzD(item("Qty"))

            If cumQty > NIGHT_LIMIT_QTY Then
                overLocked = True
            End If
        Else
            carryToDay.Add item
        End If
    Next i

    Set ApplyNightCut = outCol
End Function

Private Function ConvertCarryToDay(ByVal carryItems As Collection) As Collection
    Dim outCol As New Collection
    Dim i As Long
    Dim src As Object
    Dim dst As Object
    Dim k As Variant

    For i = 1 To carryItems.Count
        Set src = carryItems(i)
        Set dst = CreateObject("Scripting.Dictionary")

        For Each k In src.Keys
            dst(k) = src(k)
        Next k

        dst("ShiftType") = "DAY"
        dst("TimeText") = "12:00"
        dst("CarryFlag") = True
        outCol.Add dst
    Next i

    Set ConvertCarryToDay = outCol
End Function

' =========================================================
' 결과 시트 출력
' =========================================================
Private Sub WriteResultSheet(ByVal wsRes As Worksheet, ByVal nightItems As Collection, ByVal dayItems As Collection)
    Dim r As Long
    Dim i As Long

    WriteResultHeader wsRes
    r = 2

    For i = 1 To nightItems.Count
        WriteResultRowOut wsRes, r, nightItems(i)
        r = r + 1
    Next i

    For i = 1 To dayItems.Count
        WriteResultRowOut wsRes, r, dayItems(i)
        r = r + 1
    Next i
End Sub

Private Sub WriteResultHeader(ByVal ws As Worksheet)
    ws.Cells.ClearContents

    ws.Range("A1").Value = "KIND"
    ws.Range("B1").Value = "SUB_PART"
    ws.Range("C1").Value = "TIME_TEXT"
    ws.Range("D1").Value = "QTY"
    ws.Range("E1").Value = "ORDER_QTY"
    ws.Range("F1").Value = "CAR_TYPE"
    ws.Range("G1").Value = "PART_NO"
    ws.Range("H1").Value = "MODULE_PART"
    ws.Range("I1").Value = "SENSE_SPEC"
    ws.Range("J1").Value = "SENSE_LOC"
    ws.Range("K1").Value = "HOUSING"
    ws.Range("L1").Value = "HOLDER"
    ws.Range("M1").Value = "TORSION"
    ws.Range("N1").Value = "TORSION_LOC"
    ws.Range("O1").Value = "FRAME_LOC"
    ws.Range("P1").Value = "NOTE"
    ws.Range("Q1").Value = "PI_TYPE"
    ws.Range("R1").Value = "PLL_FLAG"
    ws.Range("S1").Value = "TORSION_NUM"
    ws.Range("T1").Value = "MODEL_GROUP"
    ws.Range("U1").Value = "CAR_FAMILY"
    ws.Range("V1").Value = "PTRAY_FLAG"
    ws.Range("W1").Value = "ANGLE_KEY"
    ws.Range("X1").Value = "DIR_KEY"
    ws.Range("Y1").Value = "PI_RANK"
    ws.Range("Z1").Value = "TORSION_RANK"
    ws.Range("AA1").Value = "ACTUAL_MODEL"
    ws.Range("AB1").Value = "CARRY_FLAG"
    ws.Range("AC1").Value = "PLAN_KEY"
End Sub

Private Sub WriteResultRowOut(ByVal ws As Worksheet, ByVal r As Long, ByVal item As Object)
    ws.Cells(r, "A").Value = item("ShiftType")
    ws.Cells(r, "B").Value = item("SubPart")
    ws.Cells(r, "C").Value = item("TimeText")
    ws.Cells(r, "D").Value = item("Qty")
    ws.Cells(r, "E").Value = item("Qty")
    ws.Cells(r, "F").Value = item("CarType")
    ws.Cells(r, "G").Value = item("PartNo")
    ws.Cells(r, "H").Value = item("ModulePart")
    ws.Cells(r, "I").Value = item("SenseSpec")
    ws.Cells(r, "J").Value = item("SenseLoc")
    ws.Cells(r, "K").Value = item("Housing")
    ws.Cells(r, "L").Value = item("Holder")
    ws.Cells(r, "M").Value = item("TorsionText")
    ws.Cells(r, "N").Value = item("TorsionLoc")
    ws.Cells(r, "O").Value = item("FrameLoc")
    ws.Cells(r, "P").Value = item("NoteText")
    ws.Cells(r, "Q").Value = item("PiType")
    ws.Cells(r, "R").Value = IIf(CBool(item("IsPLL")), "PLL", "GEN")
    ws.Cells(r, "S").Value = item("TorsionNum")
    ws.Cells(r, "T").Value = item("ModelGroup")
    ws.Cells(r, "U").Value = item("CarFamily")
    ws.Cells(r, "V").Value = IIf(CBool(item("PTrayFlag")), "PTRAY", "GEN")
    ws.Cells(r, "W").Value = item("AngleKey")
    ws.Cells(r, "X").Value = item("DirectionKey")
    ws.Cells(r, "Y").Value = GetPiRankByUserRule(item("PiType"), item("SubPart"))
    ws.Cells(r, "Z").Value = GetTorsionRankByUserRule(item("PiType"), item("TorsionNum"))
    ws.Cells(r, "AA").Value = item("ActualModel")
    ws.Cells(r, "AB").Value = IIf(CBool(item("CarryFlag")), "Y", "")
    ws.Cells(r, "AC").Value = item("PlanKey")
End Sub

' =========================================================
' 생산계획 반영
' =========================================================
Private Sub ApplyResultToPlan(ByVal wsRes As Worksheet, ByVal wsPlan As Worksheet)
    Dim lastRow As Long
    Dim r As Long
    Dim nightRow As Long
    Dim dayRow As Long
    Dim kind As String
    Dim qty As Double
    Dim isCarry As Boolean

    ClearPlanOutput wsPlan

    lastRow = wsRes.Cells(wsRes.Rows.Count, "A").End(xlUp).Row
    nightRow = NIGHT_DATA_START
    dayRow = DAY_DATA_START

    For r = 2 To lastRow
        kind = Trim$(CStr(wsRes.Cells(r, "A").Value))
        qty = NzD(wsRes.Cells(r, "E").Value)
        isCarry = (UCase$(Trim$(CStr(wsRes.Cells(r, "AB").Value))) = "Y")

        If kind = "NIGHT" Then
            If nightRow <= NIGHT_DATA_END Then
                WritePlanRow wsPlan, nightRow, wsRes.Cells(r, "B").Value, wsRes.Cells(r, "C").Value, qty, isCarry, CStr(wsRes.Cells(r, "AC").Value)
                nightRow = nightRow + 1
            End If

        ElseIf kind = "DAY" Then
            If dayRow <= DAY_DATA_END Then
                WritePlanRow wsPlan, dayRow, wsRes.Cells(r, "B").Value, wsRes.Cells(r, "C").Value, qty, isCarry, CStr(wsRes.Cells(r, "AC").Value)
                dayRow = dayRow + 1
            End If
        End If
    Next r

    SyncPlanStoredOrder wsPlan
End Sub

Private Sub WritePlanRow(ByVal ws As Worksheet, ByVal targetRow As Long, ByVal partNo As Variant, ByVal tm As Variant, ByVal orderQty As Variant, ByVal isCarry As Boolean, ByVal planKey As String)
    ws.Cells(targetRow, COL_PLAN_SUB).Value = partNo
    ws.Cells(targetRow, COL_PLAN_STORE_KEY).Value = planKey

    If isCarry Then
        ws.Cells(targetRow, COL_PLAN_CARRY).Value = orderQty
    Else
        ws.Cells(targetRow, COL_PLAN_CARRY).ClearContents
    End If
End Sub

Private Sub WritePlanTotals(ByVal ws As Worksheet)
    ' 합계는 시트 수식 사용
End Sub

Private Sub HideBlankPlanRows(ByVal ws As Worksheet)
    Dim r As Long

    For r = NIGHT_DATA_START To NIGHT_DATA_END
        ws.Rows(r).Hidden = (Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) = 0)
    Next r

    For r = DAY_DATA_START To DAY_DATA_END
        ws.Rows(r).Hidden = (Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) = 0)
    Next r

    ws.Rows(NIGHT_TOTAL_ROW).Hidden = False
    ws.Rows(DAY_TITLE_ROW).Hidden = False
    ws.Rows(DAY_HEADER_ROW).Hidden = False
    ws.Rows(DAY_TOTAL_ROW_1).Hidden = False
    ws.Rows(DAY_TOTAL_ROW_2).Hidden = False
    ws.Rows(DAY_TOTAL_ROW_3).Hidden = False
End Sub

Private Sub ClearPlanOutput(ByVal ws As Worksheet)
    ws.Range("B3:B100,E3:E100,T3:X100").ClearContents
    ws.Range("B104:B203,E104:E203,T104:X203").ClearContents
    ws.Range("B101").ClearContents
    ws.Range("B204").ClearContents
End Sub

' =========================================================
' P/TRAY 위치 랭크
' =========================================================
Private Function GetPTrayInnerRank(ByVal torsionNum As Double, ByVal isPTray As Boolean, ByVal piType As String) As Long
    Dim is10PI As Boolean

    is10PI = (UCase$(Trim$(piType)) = "10PI")

    If IsSameTorsion(torsionNum, 4.5) Then
        If is10PI Then
            If isPTray Then
                GetPTrayInnerRank = 0
            Else
                GetPTrayInnerRank = 1
            End If
        Else
            If isPTray Then
                GetPTrayInnerRank = 1
            Else
                GetPTrayInnerRank = 0
            End If
        End If

    ElseIf IsSameTorsion(torsionNum, 4#) Then
        If is10PI Then
            If isPTray Then
                GetPTrayInnerRank = 1
            Else
                GetPTrayInnerRank = 0
            End If
        Else
            If isPTray Then
                GetPTrayInnerRank = 0
            Else
                GetPTrayInnerRank = 1
            End If
        End If

    Else
        If isPTray Then
            GetPTrayInnerRank = 0
        Else
            GetPTrayInnerRank = 1
        End If
    End If
End Function

' =========================================================
' 사용자 기준 랭크
' 823 = 10PI 바로 뒤
' =========================================================
Private Function GetPiRankByUserRule(ByVal piType As String, ByVal subPart As String) As Long
    If Trim$(subPart) = "823" Then
        GetPiRankByUserRule = 3
        Exit Function
    End If

    Select Case UCase$(Trim$(piType))
        Case "8PI":  GetPiRankByUserRule = 1
        Case "10PI": GetPiRankByUserRule = 2
        Case Else:   GetPiRankByUserRule = 9
    End Select
End Function

Private Function GetTorsionRankByUserRule(ByVal piType As String, ByVal torsionNum As Double) As Long
    Select Case UCase$(Trim$(piType))
        Case "8PI"
            GetTorsionRankByUserRule = Get8PiTorsionRank(torsionNum)
        Case "10PI"
            GetTorsionRankByUserRule = Get10PiTorsionRank(torsionNum)
        Case Else
            GetTorsionRankByUserRule = 999
    End Select
End Function

Private Function Get8PiTorsionRank(ByVal torsionNum As Double) As Long
    If IsSameTorsion(torsionNum, 4.5) Then
        Get8PiTorsionRank = 1
    ElseIf IsSameTorsion(torsionNum, 4#) Then
        Get8PiTorsionRank = 2
    ElseIf IsSameTorsion(torsionNum, 3.5) Then
        Get8PiTorsionRank = 3
    ElseIf IsSameTorsion(torsionNum, 3#) Then
        Get8PiTorsionRank = 4
    ElseIf IsSameTorsion(torsionNum, 5#) Then
        Get8PiTorsionRank = 5
    ElseIf IsSameTorsion(torsionNum, 5.5) Then
        Get8PiTorsionRank = 6
    ElseIf IsSameTorsion(torsionNum, 7#) Then
        Get8PiTorsionRank = 7
    ElseIf torsionNum > 0 Then
        Get8PiTorsionRank = 900 + CLng(torsionNum * 10)
    Else
        Get8PiTorsionRank = 999
    End If
End Function

Private Function Get10PiTorsionRank(ByVal torsionNum As Double) As Long
    If IsSameTorsion(torsionNum, 3.5) Then
        Get10PiTorsionRank = 1
    ElseIf IsSameTorsion(torsionNum, 3#) Then
        Get10PiTorsionRank = 2
    ElseIf IsSameTorsion(torsionNum, 4#) Then
        Get10PiTorsionRank = 3
    ElseIf IsSameTorsion(torsionNum, 4.5) Then
        Get10PiTorsionRank = 4
    ElseIf torsionNum > 0 Then
        Get10PiTorsionRank = 900 + CLng(torsionNum * 10)
    Else
        Get10PiTorsionRank = 999
    End If
End Function

' =========================================================
' 각도 정규화 / 랭크
' =========================================================
Private Function NormalizeAngleKey(ByVal rawAngle As String, ByVal isPTray As Boolean) As String
    Dim s As String

    If Not isPTray Then
        NormalizeAngleKey = ""
        Exit Function
    End If

    s = UCase$(Trim$(rawAngle))
    s = Replace(s, "도", "")
    s = Replace(s, "°", "")

    Select Case s
        Case "0", "180", "270", "90"
            NormalizeAngleKey = s
        Case Else
            NormalizeAngleKey = ""
    End Select
End Function

Private Function GetAngleRankValue(ByVal angleKey As String) As Long
    Select Case UCase$(Trim$(angleKey))
        Case "0":   GetAngleRankValue = 0
        Case "180": GetAngleRankValue = 1
        Case "270": GetAngleRankValue = 2
        Case "90":  GetAngleRankValue = 3
        Case Else:  GetAngleRankValue = 9
    End Select
End Function

' =========================================================
' 기준정보 맵
' =========================================================
Private Sub BuildInfoMap(ByVal wsInfo As Worksheet, ByRef dictInfo As Object)
    mModelKeysCount = 0
    BuildModelKeys wsInfo

    Dim lastRow As Long
    Dim r As Long
    Dim key As String
    Dim arr(0 To 14) As Variant

    lastRow = wsInfo.Cells(wsInfo.Rows.Count, "A").End(xlUp).Row

    For r = 2 To lastRow
        key = Trim$(CStr(wsInfo.Cells(r, "A").Value))

        If Len(key) > 0 Then
            arr(0) = wsInfo.Cells(r, "B").Value
            arr(1) = wsInfo.Cells(r, "C").Value
            arr(2) = wsInfo.Cells(r, "E").Value
            arr(3) = wsInfo.Cells(r, "F").Value
            arr(4) = wsInfo.Cells(r, "G").Value
            arr(5) = wsInfo.Cells(r, "H").Value
            arr(6) = wsInfo.Cells(r, "I").Value
            arr(7) = wsInfo.Cells(r, "J").Value
            arr(8) = wsInfo.Cells(r, "K").Value
            arr(9) = wsInfo.Cells(r, "L").Value
            arr(10) = wsInfo.Cells(r, "M").Value
            arr(11) = wsInfo.Cells(r, "W").Value
            arr(12) = wsInfo.Cells(r, "X").Value
            arr(13) = wsInfo.Cells(r, "P").Value
            arr(14) = wsInfo.Cells(r, "R").Value

            dictInfo(key) = arr
        End If
    Next r
End Sub

Private Function GetInfoArray(ByVal infoMap As Object, ByVal subPart As String) As Variant
    If infoMap.Exists(subPart) Then
        GetInfoArray = infoMap(subPart)
    Else
        GetInfoArray = EmptyInfoArray()
    End If
End Function

Private Function EmptyInfoArray() As Variant
    EmptyInfoArray = Array("", "", "", "", "", "", "", "", "", "", "", "", "", "", "")
End Function

' =========================================================
' 파서
' =========================================================
Private Function GetPiType(ByVal txtAll As String) As String
    Dim u As String

    u = UCase$(txtAll)

    If InStr(1, u, "8PI", vbTextCompare) > 0 Then
        GetPiType = "8PI"
    ElseIf InStr(1, u, "10PI", vbTextCompare) > 0 Then
        GetPiType = "10PI"
    Else
        GetPiType = "OTHER"
    End If
End Function

Private Function IsPLLText(ByVal txt As String) As Boolean
    IsPLLText = (InStr(1, UCase$(txt), "PLL", vbTextCompare) > 0)
End Function

' =========================================================
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


Private Function GetModelGroup(ByVal carTypeText As String) As String
    Dim key As String
    Dim i As Long

    If mModelKeysCount = 0 Then
        GetModelGroup = "UNKNOWN_MODEL"
        Exit Function
    End If

    key = ExtractLeadingAlphaNum(carTypeText)

    If Len(key) = 0 Then
        GetModelGroup = "UNKNOWN_MODEL"
        Exit Function
    End If

    For i = 1 To mModelKeysCount
        If StrComp(key, mModelKeys(i), vbTextCompare) = 0 Then
            GetModelGroup = mModelKeys(i)
            Exit Function
        End If
    Next i

    GetModelGroup = "UNKNOWN_MODEL"
End Function

Private Function GetCarFamily(ByVal carType As String) As String
    Dim s As String
    Dim p As Long

    s = UCase$(Trim$(carType))
    p = InStr(1, s, "(")
    If p > 1 Then s = Left$(s, p - 1)
    s = Replace(s, " ", "")

    If Len(s) = 0 Then s = "UNKNOWN_CAR"
    GetCarFamily = s
End Function

Private Function GetDirectionKey(ByVal txt As String) As String
    Dim u As String

    u = UCase$(txt)

    If InStr(1, u, "LH", vbTextCompare) > 0 Then
        GetDirectionKey = "LH"
    ElseIf InStr(1, u, "RH", vbTextCompare) > 0 Then
        GetDirectionKey = "RH"
    Else
        GetDirectionKey = ""
    End If
End Function

Private Function IsPTrayType(ByVal src1 As String, ByVal src2 As String, ByVal src3 As String, ByVal src4 As String, ByVal src5 As String) As Boolean
    Dim u As String

    u = UCase$(src1 & " " & src2 & " " & src3 & " " & src4 & " " & src5)
    u = Replace(u, " ", "")
    u = Replace(u, "-", "")
    u = Replace(u, "_", "")

    If InStr(1, u, "P/TRAY", vbTextCompare) > 0 Then
        IsPTrayType = True
    ElseIf InStr(1, u, "PTRAY", vbTextCompare) > 0 Then
        IsPTrayType = True
    Else
        IsPTrayType = False
    End If
End Function

' =========================================================
' 백업 / 시트
' =========================================================
Private Function GetOrCreateSheet(ByVal wb As Workbook, ByVal sheetName As String) As Worksheet
    On Error Resume Next
    Set GetOrCreateSheet = wb.Worksheets(sheetName)
    On Error GoTo 0

    If GetOrCreateSheet Is Nothing Then
        Set GetOrCreateSheet = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
        GetOrCreateSheet.Name = sheetName
    End If
End Function

Private Function GetPlanBackupRange(ByVal ws As Worksheet) As Range
    Set GetPlanBackupRange = ws.Range("A1:W206")
End Function

Private Sub BackupPlanSheet(ByVal wb As Workbook)
    Dim wsPlan As Worksheet
    Dim wsBak As Worksheet
    Dim rngCopy As Range

    Set wsPlan = wb.Worksheets(SHEET_PLAN)

    On Error Resume Next
    Set wsBak = wb.Worksheets(SHEET_BACKUP)
    On Error GoTo 0

    If wsBak Is Nothing Then
        Set wsBak = wb.Worksheets.Add(After:=wb.Worksheets(wb.Worksheets.Count))
        wsBak.Name = SHEET_BACKUP
    End If

    Set rngCopy = GetPlanBackupRange(wsPlan)
    wsBak.Cells.Clear
    rngCopy.Copy
    wsBak.Range(rngCopy.Address).PasteSpecial xlPasteAll
    Application.CutCopyMode = False
End Sub

' =========================================================
' 앱 상태
' =========================================================
Private Sub SaveAppState(ByRef oldCalc As XlCalculation, ByRef oldScreen As Boolean, ByRef oldEvents As Boolean)
    oldCalc = Application.Calculation
    oldScreen = Application.ScreenUpdating
    oldEvents = Application.EnableEvents
End Sub

Private Sub RestoreAppState(ByVal oldCalc As XlCalculation, ByVal oldScreen As Boolean, ByVal oldEvents As Boolean)
    Application.ScreenUpdating = oldScreen
    Application.EnableEvents = oldEvents
    Application.Calculation = oldCalc
    Application.CutCopyMode = False
End Sub

' =========================================================
' 공용 유틸
' =========================================================
Private Sub AppendCollection(ByVal dest As Collection, ByVal src As Collection)
    Dim i As Long

    For i = 1 To src.Count
        dest.Add src(i)
    Next i
End Sub

Private Function CompareVariant(ByVal a As Variant, ByVal b As Variant) As Long
    If VarType(a) = vbString Or VarType(b) = vbString Then
        If CStr(a) < CStr(b) Then
            CompareVariant = -1
        ElseIf CStr(a) > CStr(b) Then
            CompareVariant = 1
        Else
            CompareVariant = 0
        End If
    Else
        If CDbl(a) < CDbl(b) Then
            CompareVariant = -1
        ElseIf CDbl(a) > CDbl(b) Then
            CompareVariant = 1
        Else
            CompareVariant = 0
        End If
    End If
End Function

Private Function CompareSubPart(ByVal a As String, ByVal b As String) As Long
    If IsNumeric(a) And IsNumeric(b) Then
        CompareSubPart = CompareVariant(CDbl(a), CDbl(b))
    Else
        CompareSubPart = CompareVariant(CleanKey(a), CleanKey(b))
    End If
End Function

Private Function CleanKey(ByVal v As Variant) As String
    CleanKey = UCase$(Trim$(Replace(Replace(CStr(v), vbCr, " "), vbLf, " ")))
End Function

Private Function IsSameTorsion(ByVal a As Double, ByVal b As Double) As Boolean
    IsSameTorsion = (Abs(a - b) < 0.01)
End Function

Private Function GetTorsionNumber(ByVal txt As String) As Double
    Dim i As Long
    Dim ch As String
    Dim s As String

    s = ""

    For i = 1 To Len(txt)
        ch = Mid$(txt, i, 1)
        If (ch >= "0" And ch <= "9") Or ch = "." Then
            s = s & ch
        Else
            If Len(s) > 0 Then Exit For
        End If
    Next i

    If Len(s) > 0 Then
        GetTorsionNumber = CDbl(s)
    Else
        GetTorsionNumber = 0
    End If
End Function

Private Function NzD(ByVal v As Variant) As Double
    If IsError(v) Then
        NzD = 0
    ElseIf IsNumeric(v) Then
        NzD = CDbl(v)
    ElseIf Len(Trim$(CStr(v))) = 0 Then
        NzD = 0
    Else
        NzD = 0
    End If
End Function

Private Function NzS(ByVal v As Variant) As String
    If IsError(v) Or IsNull(v) Or IsEmpty(v) Then
        NzS = ""
    Else
        NzS = Trim$(CStr(v))
    End If
End Function

Private Function NormalizeKey(ByVal v As Variant) As String
    If IsError(v) Or IsNull(v) Or IsEmpty(v) Then
        NormalizeKey = ""
    Else
        NormalizeKey = UCase$(Trim$(CStr(v)))
    End If
End Function

' =========================================================
' 수동서열 반영 코어
' V열(구간), W열(목표순번)
' B/E/G/T만 재배치
' =========================================================
Private Sub ApplyManualSeqCore()
    Dim wb As Workbook
    Dim wsPlan As Worksheet
    Dim oldCalc As XlCalculation
    Dim oldScreen As Boolean
    Dim oldEvents As Boolean
    Dim appliedCount As Long

    On Error GoTo EH

    Set wb = ThisWorkbook
    Set wsPlan = wb.Worksheets(SHEET_PLAN)

    SaveAppState oldCalc, oldScreen, oldEvents
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    ApplyStoredOrderFromColumns wsPlan, True, appliedCount

    If appliedCount > 0 Then
        MsgBox "저장서열 반영 완료 : " & appliedCount & "건", vbInformation
    End If

SAFE_EXIT:
    RestoreAppState oldCalc, oldScreen, oldEvents
    Exit Sub

EH:
    MsgBox "APPLY_MANUAL_SEQ 오류: " & Err.Description, vbExclamation
    Resume SAFE_EXIT
End Sub

Public Sub SyncPlanStoredOrder(ByVal ws As Worksheet)
    Dim r As Long
    Dim seqNo As Long

    seqNo = 1
    For r = NIGHT_DATA_START To NIGHT_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            ws.Cells(r, COL_PLAN_SEQ).Value = seqNo
            ws.Cells(r, COL_PLAN_MANUAL_SEC).Value = "야간"
            ws.Cells(r, COL_PLAN_MANUAL_SEQ).Value = seqNo
            If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_STORE_KEY).Value))) = 0 Then
                ws.Cells(r, COL_PLAN_STORE_KEY).Value = BuildLegacyPlanKey("NIGHT", ws.Cells(r, COL_PLAN_SUB).Value, ws.Cells(r, COL_PLAN_TIME).Value, seqNo)
            End If
            seqNo = seqNo + 1
        Else
            ws.Cells(r, COL_PLAN_SEQ).ClearContents
            ws.Cells(r, COL_PLAN_MANUAL_SEC).ClearContents
            ws.Cells(r, COL_PLAN_MANUAL_SEQ).ClearContents
            ws.Cells(r, COL_PLAN_STORE_KEY).ClearContents
        End If
    Next r

    seqNo = 1
    For r = DAY_DATA_START To DAY_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            ws.Cells(r, COL_PLAN_SEQ).Value = seqNo
            ws.Cells(r, COL_PLAN_MANUAL_SEC).Value = "주간"
            ws.Cells(r, COL_PLAN_MANUAL_SEQ).Value = seqNo
            If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_STORE_KEY).Value))) = 0 Then
                ws.Cells(r, COL_PLAN_STORE_KEY).Value = BuildLegacyPlanKey("DAY", ws.Cells(r, COL_PLAN_SUB).Value, ws.Cells(r, COL_PLAN_TIME).Value, seqNo)
            End If
            seqNo = seqNo + 1
        Else
            ws.Cells(r, COL_PLAN_SEQ).ClearContents
            ws.Cells(r, COL_PLAN_MANUAL_SEC).ClearContents
            ws.Cells(r, COL_PLAN_MANUAL_SEQ).ClearContents
            ws.Cells(r, COL_PLAN_STORE_KEY).ClearContents
        End If
    Next r

    HideBlankPlanRows ws
End Sub

Private Sub SnapshotStoredOrder(ByVal ws As Worksheet, ByRef snap As Object)
    Dim r As Long
    Dim key As String
    Dim secText As String
    Dim seqNo As Long

    snap.RemoveAll

    For r = NIGHT_DATA_START To NIGHT_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            key = Trim$(CStr(ws.Cells(r, COL_PLAN_STORE_KEY).Value))
            If Len(key) = 0 Then key = BuildLegacyPlanKey("NIGHT", ws.Cells(r, COL_PLAN_SUB).Value, ws.Cells(r, COL_PLAN_TIME).Value, r - NIGHT_DATA_START + 1)

            secText = NormalizeManualSection(CStr(ws.Cells(r, COL_PLAN_MANUAL_SEC).Value))
            If Len(secText) = 0 Then secText = "NIGHT"

            seqNo = ParsePositiveLong(ws.Cells(r, COL_PLAN_MANUAL_SEQ).Value)
            If seqNo <= 0 Then seqNo = r - NIGHT_DATA_START + 1

            snap(key) = Array(secText, seqNo)
        End If
    Next r

    For r = DAY_DATA_START To DAY_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            key = Trim$(CStr(ws.Cells(r, COL_PLAN_STORE_KEY).Value))
            If Len(key) = 0 Then key = BuildLegacyPlanKey("DAY", ws.Cells(r, COL_PLAN_SUB).Value, ws.Cells(r, COL_PLAN_TIME).Value, r - DAY_DATA_START + 1)

            secText = NormalizeManualSection(CStr(ws.Cells(r, COL_PLAN_MANUAL_SEC).Value))
            If Len(secText) = 0 Then secText = "DAY"

            seqNo = ParsePositiveLong(ws.Cells(r, COL_PLAN_MANUAL_SEQ).Value)
            If seqNo <= 0 Then seqNo = r - DAY_DATA_START + 1

            snap(key) = Array(secText, seqNo)
        End If
    Next r
End Sub

Private Sub RestoreStoredOrderFromSnapshot(ByVal ws As Worksheet, ByVal snap As Object, ByRef restoredCount As Long)
    Dim allRecs As Collection
    Dim rec As Object
    Dim nightCol As Collection
    Dim dayCol As Collection
    Dim vals As Variant
    Dim i As Long

    restoredCount = 0
    Set allRecs = CollectPlanRecords(ws)

    If allRecs.Count = 0 Then
        SyncPlanStoredOrder ws
        Exit Sub
    End If

    For i = 1 To allRecs.Count
        Set rec = allRecs(i)

        If snap.Exists(CStr(rec("PlanKey"))) Then
            vals = snap(CStr(rec("PlanKey")))
            rec("StoredSec") = CStr(vals(0))
            rec("StoredSeq") = CLng(vals(1))
            restoredCount = restoredCount + 1
        Else
            rec("StoredSec") = CStr(rec("CurrentSec"))
            rec("StoredSeq") = 100000 + CLng(rec("NaturalOrder"))
        End If
    Next i

    Set nightCol = ExtractSectionRecords(allRecs, "NIGHT")
    Set dayCol = ExtractSectionRecords(allRecs, "DAY")

    Set nightCol = SortPlanRecords(nightCol)
    Set dayCol = SortPlanRecords(dayCol)
    BalancePlanCollections nightCol, dayCol

    RewritePlanFromCollections ws, nightCol, dayCol
    SyncPlanStoredOrder ws
End Sub

Private Sub ApplyStoredOrderFromColumns(ByVal ws As Worksheet, ByVal showNoInputMsg As Boolean, ByRef appliedCount As Long)
    Dim allRecs As Collection
    Dim rec As Object
    Dim nightCol As Collection
    Dim dayCol As Collection
    Dim i As Long
    Dim hasInput As Boolean
    Dim secText As String
    Dim seqNo As Long

    appliedCount = 0
    Set allRecs = CollectPlanRecords(ws)

    If allRecs.Count = 0 Then
        If showNoInputMsg Then MsgBox "생산계획 데이터가 없습니다.", vbInformation
        Exit Sub
    End If

    For i = 1 To allRecs.Count
        Set rec = allRecs(i)
        secText = NormalizeManualSection(CStr(rec("InputSec")))
        seqNo = ParsePositiveLong(rec("InputSeq"))

        If Len(secText) > 0 Or seqNo > 0 Then hasInput = True

        If Len(secText) = 0 Then secText = CStr(rec("CurrentSec"))
        If seqNo <= 0 Then seqNo = 100000 + CLng(rec("NaturalOrder"))

        rec("StoredSec") = secText
        rec("StoredSeq") = seqNo
    Next i

    If Not hasInput Then
        If showNoInputMsg Then
            MsgBox "적용할 저장서열 입력값이 없습니다. V열(야간/주간), W열(순번)을 확인하세요.", vbInformation
        End If
        Exit Sub
    End If

    Set nightCol = ExtractSectionRecords(allRecs, "NIGHT")
    Set dayCol = ExtractSectionRecords(allRecs, "DAY")

    Set nightCol = SortPlanRecords(nightCol)
    Set dayCol = SortPlanRecords(dayCol)
    BalancePlanCollections nightCol, dayCol

    RewritePlanFromCollections ws, nightCol, dayCol
    SyncPlanStoredOrder ws

    appliedCount = allRecs.Count
End Sub

Private Function CollectPlanRecords(ByVal ws As Worksheet) As Collection
    Dim col As New Collection
    Dim r As Long
    Dim naturalOrder As Long

    naturalOrder = 0

    For r = NIGHT_DATA_START To NIGHT_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            naturalOrder = naturalOrder + 1
            col.Add MakePlanRecord(ws, r, "NIGHT", naturalOrder)
        End If
    Next r

    For r = DAY_DATA_START To DAY_DATA_END
        If Len(Trim$(CStr(ws.Cells(r, COL_PLAN_SUB).Value))) > 0 Then
            naturalOrder = naturalOrder + 1
            col.Add MakePlanRecord(ws, r, "DAY", naturalOrder)
        End If
    Next r

    Set CollectPlanRecords = col
End Function

Private Function MakePlanRecord(ByVal ws As Worksheet, ByVal r As Long, ByVal currentSec As String, ByVal naturalOrder As Long) As Object
    Dim rec As Object
    Dim keyText As String

    Set rec = CreateObject("Scripting.Dictionary")

    keyText = Trim$(CStr(ws.Cells(r, COL_PLAN_STORE_KEY).Value))
    If Len(keyText) = 0 Then
        keyText = BuildLegacyPlanKey(currentSec, ws.Cells(r, COL_PLAN_SUB).Value, ws.Cells(r, COL_PLAN_TIME).Value, naturalOrder)
    End If

    rec("SeqVal") = ws.Cells(r, COL_PLAN_SEQ).Value
    rec("SubPart") = ws.Cells(r, COL_PLAN_SUB).Value
    rec("TimeText") = ws.Cells(r, COL_PLAN_TIME).Value
    rec("CarryVal") = ws.Cells(r, COL_PLAN_CARRY).Value
    rec("PlanKey") = keyText
    rec("CurrentSec") = currentSec
    rec("NaturalOrder") = naturalOrder
    rec("InputSec") = ws.Cells(r, COL_PLAN_MANUAL_SEC).Value
    rec("InputSeq") = ws.Cells(r, COL_PLAN_MANUAL_SEQ).Value

    Set MakePlanRecord = rec
End Function

Private Function ExtractSectionRecords(ByVal allRecs As Collection, ByVal secText As String) As Collection
    Dim outCol As New Collection
    Dim i As Long
    Dim rec As Object

    For i = 1 To allRecs.Count
        Set rec = allRecs(i)
        If UCase$(Trim$(CStr(rec("StoredSec")))) = UCase$(Trim$(secText)) Then
            outCol.Add rec
        End If
    Next i

    Set ExtractSectionRecords = outCol
End Function

Private Function SortPlanRecords(ByVal src As Collection) As Collection
    Dim outCol As New Collection
    Dim arr() As Object
    Dim i As Long
    Dim j As Long
    Dim tmp As Object

    If src Is Nothing Then
        Set SortPlanRecords = outCol
        Exit Function
    End If

    If src.Count = 0 Then
        Set SortPlanRecords = outCol
        Exit Function
    End If

    ReDim arr(1 To src.Count)
    For i = 1 To src.Count
        Set arr(i) = src(i)
    Next i

    For i = 1 To UBound(arr) - 1
        For j = i + 1 To UBound(arr)
            If ComparePlanRecord(arr(i), arr(j)) > 0 Then
                Set tmp = arr(i)
                Set arr(i) = arr(j)
                Set arr(j) = tmp
            End If
        Next j
    Next i

    For i = 1 To UBound(arr)
        outCol.Add arr(i)
    Next i

    Set SortPlanRecords = outCol
End Function

Private Function ComparePlanRecord(ByVal a As Object, ByVal b As Object) As Long
    Dim sa As Long
    Dim sb As Long
    Dim na As Long
    Dim nb As Long

    sa = CLng(a("StoredSeq"))
    sb = CLng(b("StoredSeq"))

    If sa < sb Then
        ComparePlanRecord = -1
        Exit Function
    ElseIf sa > sb Then
        ComparePlanRecord = 1
        Exit Function
    End If

    na = CLng(a("NaturalOrder"))
    nb = CLng(b("NaturalOrder"))

    If na < nb Then
        ComparePlanRecord = -1
    ElseIf na > nb Then
        ComparePlanRecord = 1
    Else
        ComparePlanRecord = 0
    End If
End Function

Private Sub BalancePlanCollections(ByRef nightCol As Collection, ByRef dayCol As Collection)
    Dim nightCap As Long
    Dim dayCap As Long
    Dim nightKeep As Collection
    Dim nightOverflow As Collection
    Dim dayKeep As Collection
    Dim dayOverflow As Collection
    Dim dayTemp As Collection

    nightCap = NIGHT_DATA_END - NIGHT_DATA_START + 1
    dayCap = DAY_DATA_END - DAY_DATA_START + 1

    Set nightKeep = FirstNRecords(nightCol, nightCap)
    Set nightOverflow = SkipNRecords(nightCol, nightCap)

    Set dayTemp = MergeRecordCollections(nightOverflow, dayCol)
    Set dayKeep = FirstNRecords(dayTemp, dayCap)
    Set dayOverflow = SkipNRecords(dayTemp, dayCap)

    Set nightCol = MergeRecordCollections(nightKeep, dayOverflow)
    Set dayCol = dayKeep
End Sub

Private Function FirstNRecords(ByVal src As Collection, ByVal takeCount As Long) As Collection
    Dim outCol As New Collection
    Dim i As Long

    If src Is Nothing Then
        Set FirstNRecords = outCol
        Exit Function
    End If

    For i = 1 To src.Count
        If i > takeCount Then Exit For
        outCol.Add src(i)
    Next i

    Set FirstNRecords = outCol
End Function

Private Function SkipNRecords(ByVal src As Collection, ByVal skipCount As Long) As Collection
    Dim outCol As New Collection
    Dim i As Long

    If src Is Nothing Then
        Set SkipNRecords = outCol
        Exit Function
    End If

    For i = 1 To src.Count
        If i > skipCount Then
            outCol.Add src(i)
        End If
    Next i

    Set SkipNRecords = outCol
End Function

Private Function MergeRecordCollections(ByVal firstCol As Collection, ByVal secondCol As Collection) As Collection
    Dim outCol As New Collection
    Dim i As Long

    If Not firstCol Is Nothing Then
        For i = 1 To firstCol.Count
            outCol.Add firstCol(i)
        Next i
    End If

    If Not secondCol Is Nothing Then
        For i = 1 To secondCol.Count
            outCol.Add secondCol(i)
        Next i
    End If

    Set MergeRecordCollections = outCol
End Function

Private Sub RewritePlanFromCollections(ByVal ws As Worksheet, ByVal nightCol As Collection, ByVal dayCol As Collection)
    Dim i As Long
    Dim targetRow As Long

    ClearPlanOutput ws

    targetRow = NIGHT_DATA_START
    If Not nightCol Is Nothing Then
        For i = 1 To nightCol.Count
            If targetRow > NIGHT_DATA_END Then Exit For
            WritePlanRecordFromObject ws, targetRow, nightCol(i)
            targetRow = targetRow + 1
        Next i
    End If

    targetRow = DAY_DATA_START
    If Not dayCol Is Nothing Then
        For i = 1 To dayCol.Count
            If targetRow > DAY_DATA_END Then Exit For
            WritePlanRecordFromObject ws, targetRow, dayCol(i)
            targetRow = targetRow + 1
        Next i
    End If
End Sub

Private Sub WritePlanRecordFromObject(ByVal ws As Worksheet, ByVal targetRow As Long, ByVal rec As Object)
    ws.Cells(targetRow, COL_PLAN_SUB).Value = rec("SubPart")

    If Len(Trim$(CStr(rec("CarryVal")))) > 0 Then
        ws.Cells(targetRow, COL_PLAN_CARRY).Value = rec("CarryVal")
    Else
        ws.Cells(targetRow, COL_PLAN_CARRY).ClearContents
    End If

    ws.Cells(targetRow, COL_PLAN_STORE_KEY).Value = rec("PlanKey")
End Sub

Private Function NormalizeManualSection(ByVal v As String) As String
    Dim s As String

    s = UCase$(Trim$(v))
    s = Replace(s, " ", "")

    Select Case s
        Case "야", "야간", "N", "NIGHT"
            NormalizeManualSection = "NIGHT"
        Case "주", "주간", "D", "DAY"
            NormalizeManualSection = "DAY"
        Case Else
            NormalizeManualSection = ""
    End Select
End Function

Private Function ParsePositiveLong(ByVal v As Variant) As Long
    If IsNumeric(v) Then
        If CLng(v) > 0 Then
            ParsePositiveLong = CLng(v)
        Else
            ParsePositiveLong = 0
        End If
    Else
        ParsePositiveLong = 0
    End If
End Function

Private Function BuildLegacyPlanKey(ByVal secText As String, ByVal subPart As Variant, ByVal timeText As Variant, ByVal seqNo As Long) As String
    BuildLegacyPlanKey = "LEGACY|" & UCase$(Trim$(secText)) & "|" & Trim$(CStr(subPart)) & "|" & Trim$(CStr(timeText)) & "|" & Format$(seqNo, "00000")
End Function


