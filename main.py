import json
import time
from pathlib import Path

# Mini NPU Simulator
# 2단계: 사용자 입력과 오류 처리

EPSILON = 1e-9


def mac(pattern, filter_data):
    score = 0.0

    for i in range(len(pattern)):
        for j in range(len(pattern[i])):
            score += pattern[i][j] * filter_data[i][j]

    return score


def input_matrix(name, size=3):
    """사용자로부터 size x size 숫자 배열을 입력받는다."""
    print(f"\n{name} ({size}줄 입력, 공백 구분)")

    matrix = []

    while len(matrix) < size:
        row_number = len(matrix) + 1
        user_input = input(f"{row_number}행: ")

        try:
            row = [float(x) for x in user_input.split()]

            if len(row) != size:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                continue

            matrix.append(row)

        except ValueError:
            print("입력 오류: 숫자만 입력하세요.")

    return matrix


def classify(score_a, score_b):
    """허용오차를 적용하여 두 점수를 비교한다."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"

    if score_a > score_b:
        return "A"

    return "B"


def normalize_label(label):
    """다양한 라벨을 Cross와 X로 통일한다."""
    if not isinstance(label, str):
        raise ValueError("라벨이 문자열이 아닙니다.")

    label = label.strip().lower()

    if label in ("+", "cross"):
        return "Cross"

    if label == "x":
        return "X"

    raise ValueError(f"알 수 없는 라벨: {label}")


def validate_matrix(matrix, size):
    """행렬이 올바른 크기와 숫자로 구성됐는지 확인한다."""
    if not isinstance(matrix, list) or len(matrix) != size:
        raise ValueError(f"행 개수가 {size}개가 아닙니다.")

    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(f"열 개수가 {size}개가 아닙니다.")

        for value in row:
            if type(value) not in (int, float):
                raise ValueError("숫자가 아닌 값이 있습니다.")


def analyze_json():
    """data.json의 패턴을 분석하고 PASS/FAIL을 출력한다."""
    print("\n=== data.json 분석 ===")

    data_path = Path(__file__).resolve().parent / "data.json"

    try:
        with data_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)

        filters = data["filters"]
        patterns = data["patterns"]

        if not isinstance(filters, dict):
            raise ValueError("filters는 객체여야 합니다.")

        if not isinstance(patterns, dict):
            raise ValueError("patterns는 객체여야 합니다.")

    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"파일 로드 오류: {error}")
        return

    total = 0
    passed = 0
    failures = []

    print("\n[1] 패턴 분석")

    for case_id, case in patterns.items():
        total += 1
        print(f"\n--- {case_id} ---")

        try:
            parts = case_id.split("_")

            if len(parts) != 3 or parts[0] != "size":
                raise ValueError("잘못된 케이스 키 형식")

            size = int(parts[1])

            if size not in (5, 13, 25):
                raise ValueError("지원하지 않는 크기")

            filter_group = filters[f"size_{size}"]

            cross_filter = filter_group["cross"]
            x_filter = filter_group["x"]

            pattern = case["input"]
            expected = normalize_label(case["expected"])

            validate_matrix(cross_filter, size)
            validate_matrix(x_filter, size)
            validate_matrix(pattern, size)

            cross_score = mac(pattern, cross_filter)
            x_score = mac(pattern, x_filter)

            if abs(cross_score - x_score) < EPSILON:
                result = "UNDECIDED"
            elif cross_score > x_score:
                result = "Cross"
            else:
                result = "X"

            print(f"Cross 점수: {cross_score:.12f}")
            print(f"X 점수: {x_score:.12f}")
            print(f"판정: {result}")
            print(f"expected: {expected}")

            if result == expected:
                print("결과: PASS")
                passed += 1
            else:
                reason = (
                    "허용오차에 따른 동점 판정"
                    if result == "UNDECIDED"
                    else "예상 라벨과 판정 결과 불일치"
                )
                print(f"결과: FAIL ({reason})")
                failures.append((case_id, reason))

        except (ValueError, KeyError, TypeError, IndexError) as error:
            reason = f"데이터/스키마 오류: {error}"
            print(f"결과: FAIL ({reason})")
            failures.append((case_id, reason))

    print("\n[2] 결과 요약")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {len(failures)}개")

    if failures:
        print("\n실패 케이스:")
        for case_id, reason in failures:
            print(f"- {case_id}: {reason}")

    performance_test([3, 5, 13, 25])


def performance_test(sizes, repeats=10):
    """크기별 MAC 연산 시간을 반복 측정한다."""

    print(f"\n[성능 분석] 평균/{repeats}회")
    print(f"{'크기':<12}{'평균 시간(ms)':<18}{'연산 횟수':<12}")
    print("-" * 42)

    for size in sizes:
        # 성능 측정에 사용할 행렬 생성
        pattern = [[1.0] * size for _ in range(size)]
        filter_data = [[1.0] * size for _ in range(size)]

        # 첫 실행 준비
        mac(pattern, filter_data)

        # 시간 측정
        start = time.perf_counter()

        for _ in range(repeats):
            mac(pattern, filter_data)

        end = time.perf_counter()

        average_ms = (end - start) * 1000 / repeats
        operations = size * size

        print(
            f"{size}x{size:<9}"
            f"{average_ms:<18.6f}"
            f"{operations:<12}"
        )

def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("선택 (1/2): ").strip()

        if choice in ("1", "2"):
            break

        print("입력 오류: 1 또는 2를 선택하세요.")

    if choice == "2":
        analyze_json()
        return

    print("\n[1] 필터 입력")

    filter_a = input_matrix("필터 A")
    filter_b = input_matrix("필터 B")

    print("\n필터 저장 완료!")
    print("\n[2] 패턴 입력")

    pattern = input_matrix("패턴")

    print("\n[3] MAC 연산 결과")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    result = classify(score_a, score_b)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"판정: {result}")
    performance_test([3])

if __name__ == "__main__":
    main()