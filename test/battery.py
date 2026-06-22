import time

try:
    from gpiozero import LED
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


# ===== 설정 =====
LED_PIN = 4

# 사용하는 배터리에 맞게 수정 (만충 / 방전 전압, 단위 V)
VOLTAGE_FULL = 8.4
VOLTAGE_EMPTY = 6.0

READ_INTERVAL = 1.0   # 전압을 읽는 최소 간격(초). 매 프레임 읽지 않음 (효율)
BLINK_ON_TIME = 0.1   # 깜빡일 때 불이 켜져 있는 시간(초)


# ===== 내부 상태 =====
_led = None
_voltage_reader = None
_last_read = 0.0
_cached_percent = None
_current_blink = None   # 지금 적용된 깜빡 상태 (중복 명령 방지)


def setup(voltage_reader=None):
    """voltage_reader: 전압(float V)을 반환하는 함수. None이면 잔량/LED 동작 안 함."""
    global _led, _voltage_reader
    _voltage_reader = voltage_reader

    if _GPIO_AVAILABLE:
        _led = LED(LED_PIN)
        _led.off()


def voltage_to_percent(voltage):
    percent = (voltage - VOLTAGE_EMPTY) / (VOLTAGE_FULL - VOLTAGE_EMPTY) * 100
    return max(0, min(100, int(percent)))


def get_blink_interval(percent):
    # 깜빡 주기(초)를 반환. None = 깜빡 안 함(꺼짐).
    if percent >= 100:
        return None       # 100% : 불 안 들어옴
    elif percent >= 70:
        return 5.0        # 70 ~ 99% : 5초에 한 번
    elif percent >= 50:
        return 2.5        # 50 ~ 69% : 2.5초에 한 번
    elif percent > 25:
        return 1.5        # 25 ~ 50% : (요청에 없던 구간, 임의값 - 필요시 수정)
    else:
        return 1.0        # 25% 이하 : 1초에 한 번


def _apply_led(percent):
    global _current_blink

    if _led is None:
        return

    interval = get_blink_interval(percent)

    # 상태가 바뀔 때만 LED 명령 (매 프레임 호출해도 깜빡이 리셋되지 않게)
    if interval == _current_blink:
        return
    _current_blink = interval

    if interval is None:
        _led.off()
    else:
        off_time = max(0.05, interval - BLINK_ON_TIME)
        _led.blink(on_time=BLINK_ON_TIME, off_time=off_time, background=True)


def update():
    """루프에서 매 프레임 호출해도 됨. 내부에서 캐싱 + LED 갱신. 잔량%(또는 None) 반환."""
    global _last_read, _cached_percent

    if _voltage_reader is None:
        return None

    now = time.time()
    if now - _last_read >= READ_INTERVAL:
        _last_read = now
        voltage = _voltage_reader()
        if voltage is not None:
            _cached_percent = voltage_to_percent(voltage)
            _apply_led(_cached_percent)
    
    return _cached_percent


def cleanup():
    if _led is not None:
        _led.off()
        _led.close()

