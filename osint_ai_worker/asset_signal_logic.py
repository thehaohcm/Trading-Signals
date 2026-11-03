"""Logic thuần cho trạng thái AI NÊN/KHÔNG (không I/O) — tách riêng để unittest."""


def decide_ai_status(current, pending, pending_count, new, confirm_runs=2, first_run=False):
    """
    Hysteresis: chỉ đổi trạng thái khi AI trả cùng một kết quả mới `confirm_runs` lần chạy liên tiếp.

    Trả về (status, pending_status, pending_count):
      - lần chạy đầu tiên (hoặc chưa có trạng thái) → nhận ngay;
      - kết quả trùng trạng thái hiện tại → giữ, xoá bộ đếm chờ;
      - kết quả khác: đếm liên tiếp (đổi hướng giữa chừng thì đếm lại từ 1); đủ N lần → đổi.
    """
    if first_run or current is None:
        return new, None, 0
    if new == current:
        return current, None, 0
    count = (pending_count or 0) + 1 if pending == new else 1
    if count >= max(1, int(confirm_runs)):
        return new, None, 0
    return current, new, count
