# [EXPERIMENT] VELOS 모니터링 유틸리티 - 시스템 모니터링 모듈
# [EXPERIMENT] monitor_utils.py
from __future__ import annotations
import pandas as pd
from typing import Iterable, Optional, Union, Literal

ColumnKeys = Union[str, Iterable[str]]
ConflictPolicy = Literal["keep_left", "keep_right", "suffix", "raise"]


def with_prefix(df: pd.DataFrame, prefix: str, *, sep: str = ".") -> pd.DataFrame:
    """
    모든 컬럼명에 {prefix}{sep}{col} 형태로 프리픽스를 붙인 새 DataFrame을 반환.
    원본 df는 변경하지 않음.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("with_prefix: df must be a pandas DataFrame")
    if not prefix:
        return df.copy()

    out = df.copy()
    out.columns = [f"{prefix}{sep}{c}" for c in out.columns]
    return out


def _ensure_dataframe(obj: Union[pd.Series, pd.DataFrame], *, name: str = "value") -> pd.DataFrame:
    """
    Series를 단일 컬럼 DataFrame으로 올려서
    'Cannot set a DataFrame with multiple columns to the single column' 류의 오류를 방지.
    """
    if isinstance(obj, pd.DataFrame):
        return obj
    if isinstance(obj, pd.Series):
        return obj.to_frame(name=name)
    raise TypeError(f"_ensure_dataframe: unsupported type {type(obj)!r}")


def _align_or_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    on: Optional[ColumnKeys] = None,
    left_on: Optional[ColumnKeys] = None,
    right_on: Optional[ColumnKeys] = None,
    how: str = "left",
) -> pd.DataFrame:
    """
    조인 키가 없으면 index 기준으로 column-wise concat,
    키가 있으면 pandas.merge 사용.
    """
    if on is None and left_on is None and right_on is None:
        # 인덱스 정렬/동일 여부는 사용자가 보장한다고 가정.
        # 다르면 필요시 reindex로 맞추세요.
        return pd.concat([left, right], axis=1)
    else:
        return left.merge(right, how=how, on=on, left_on=left_on, right_on=right_on)


def _resolve_conflicts(
    df: pd.DataFrame,
    *,
    conflict: ConflictPolicy = "suffix",
    suffix: str = "_r",
    keep: Literal["left", "right"] = "left",
) -> pd.DataFrame:
    """
    컬럼 충돌 해결 정책:
      - keep_left: 좌측 동명 컬럼 유지(우측 삭제)
      - keep_right: 우측 동명 컬럼 유지(좌측 삭제)
      - suffix: 충돌 컬럼에 suffix 부여(우측 컬럼만)
      - raise: 충돌 시 에러
    """
    cols = pd.Series(df.columns)
    duplicates = cols[cols.duplicated(keep=False)].tolist()
    if not duplicates:
        return df

    if conflict == "raise":
        raise ValueError(f"Column conflicts found: {sorted(set(duplicates))}")

    if conflict in ("keep_left", "keep_right"):
        # 중복이 있는 모든 컬럼에 대해 하나만 남기기
        to_drop = []
        seen = set()
        for c in df.columns:
            if c in seen:
                # 이미 하나 남겼다면 이후 동일 이름은 drop
                if conflict == "keep_left":
                    to_drop.append(c)
                else:
                    # keep_right: 이전에 본 첫 컬럼 drop, 현재 컬럼 keep로 교체
                    # 이전 발견 인덱스 찾아 drop 리스트에 추가
                    prev_idx = list(df.columns).index(c)
                    # 첫 등장만 drop되도록 보정
                    # (간단화를 위해 전체 컬럼을 한 번 더 스캔)
                    mark = True
                    running = []
                    for i, name in enumerate(df.columns):
                        if name == c:
                            if mark:
                                running.append(i)
                                mark = False
                    to_drop.append(df.columns[running[0]])
            else:
                seen.add(c)
        return df.drop(columns=to_drop)

    if conflict == "suffix":
        # 동일 이름 중 뒤쪽 것들에만 suffix 부여
        new_cols = []
        seen_count = {}
        for c in df.columns:
            seen_count[c] = seen_count.get(c, 0) + 1
            if seen_count[c] == 1:
                new_cols.append(c)
            else:
                new_cols.append(f"{c}{suffix}")
        df = df.copy()
        df.columns = new_cols
        return df

    return df  # fallback


def _safe_attach(
    left: pd.DataFrame,
    right: Union[pd.Series, pd.DataFrame],
    *,
    prefix: Optional[str] = None,
    sep: str = ".",
    on: Optional[ColumnKeys] = None,
    left_on: Optional[ColumnKeys] = None,
    right_on: Optional[ColumnKeys] = None,
    how: str = "left",
    conflict: ConflictPolicy = "suffix",
    conflict_suffix: str = "_r",
) -> pd.DataFrame:
    """
    안전 병합 유틸리티.
      1) right를 DataFrame으로 보장(Series도 허용)
      2) prefix가 주어지면 우측 컬럼에 prefix 부여
      3) 키가 없으면 index 기준 concat, 있으면 merge
      4) 병합 후 컬럼 충돌 처리 정책 적용

    예)
    df2 = _safe_attach(df, feats, prefix="feat")            # 인덱스 정렬 후 컬럼 붙이기
    df2 = _safe_attach(df, other, on="id", prefix="right")  # id 조인으로 붙이고 우측 prefix
    """
    if not isinstance(left, pd.DataFrame):
        raise TypeError("_safe_attach: left must be a DataFrame")

    rdf = _ensure_dataframe(right)

    if prefix:
        rdf = with_prefix(rdf, prefix, sep=sep)

    attached = _align_or_merge(
        left, rdf, on=on, left_on=left_on, right_on=right_on, how=how
    )

    attached = _resolve_conflicts(
        attached, conflict=conflict,
        suffix=conflict_suffix,
        keep="left" if conflict == "keep_left" else "right"
    )
    return attached



