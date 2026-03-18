import pandas as pd
from src.e_score import e_score

CSV_PATH = "data/samples/labels_100.csv"  # 네 파일명에 맞게 바꿔도 됨
TITLE_COL = "title"
BODY_COL = "snippet"   # 우선 snippet으로 점수화 (원문 body가 있으면 body로 바꾸기)
LABEL_COL = "E"        # 실행가능 라벨 (0/1)

def to_int(x):
    # '1', 1, 'Y' 같은 값들이 섞여 있어도 안전하게 처리
    if pd.isna(x):
        return 0
    s = str(x).strip().lower()
    if s in ["1", "y", "yes", "true", "t"]:
        return 1
    return 0

def main():
    df = pd.read_csv(CSV_PATH)

    # 컬럼 존재 체크
    for c in [TITLE_COL, BODY_COL, LABEL_COL]:
        if c not in df.columns:
            raise ValueError(f"CSV에 '{c}' 컬럼이 없습니다. 현재 컬럼: {list(df.columns)}")

    # 라벨 정리
    df[LABEL_COL] = df[LABEL_COL].apply(to_int)

    # 점수 계산
    scores = []
    reasons_list = []
    for _, row in df.iterrows():
        title = "" if pd.isna(row[TITLE_COL]) else str(row[TITLE_COL])
        snip  = "" if pd.isna(row[BODY_COL]) else str(row[BODY_COL])

        body = snip.strip()
        if not body:
            body = title  # snippet 비어있으면 title을 body로 재사용

        s, reasons = e_score(title, body)
        scores.append(s)
        reasons_list.append(",".join(reasons))

    df["E_score"] = scores
    df["reasons"] = reasons_list

    # 그룹별 통계
    e1 = df[df[LABEL_COL] == 1]["E_score"]
    e0 = df[df[LABEL_COL] == 0]["E_score"]

    print("\n=== 그룹별 점수 통계 ===")
    print(f"E=1 개수: {len(e1)} | 평균: {e1.mean():.2f} | 중앙값: {e1.median():.2f} | 최대: {e1.max():.0f}")
    print(f"E=0 개수: {len(e0)} | 평균: {e0.mean():.2f} | 중앙값: {e0.median():.2f} | 최대: {e0.max():.0f}")

    # 커트라인 후보 평가
    print("\n=== 커트라인별 성능(대략) ===")
    for thr in [4, 6, 8, 10, 12]:
        pred = df["E_score"] >= thr
        tp = int(((pred) & (df[LABEL_COL] == 1)).sum())
        fp = int(((pred) & (df[LABEL_COL] == 0)).sum())
        fn = int((~pred & (df[LABEL_COL] == 1)).sum())

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        print(f"thr>={thr:2d} | TP={tp:3d} FP={fp:3d} FN={fn:3d} | Precision={precision:.2f} Recall={recall:.2f}")

    # 상위 후보 보기
    print("\n=== 점수 상위 15개(검토용) ===")
    top = df.sort_values("E_score", ascending=False).head(15)
    cols = ["E_score", LABEL_COL, "title", "url", "reasons"]
    cols = [c for c in cols if c in top.columns]  # url 없을 수도 있으니 안전 처리
    print(top[cols].to_string(index=False))

    # 결과 저장(선택)
    out_path = "data/samples/scored_labels_100.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n저장 완료: {out_path}")

if __name__ == "__main__":
    main()
