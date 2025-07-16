import time
from datetime import datetime, UTC
from config import (now_time, RES)

t_time = time.time()
dt_local = datetime.now().timestamp()
dt_utc = datetime.now(UTC).timestamp()
dt_manila = now_time().timestamp()

print(f"UTC >>     {dt_utc:.6f}")
print(f"LOCAL >>   {dt_local:.6f}")
print(f"TIME_TIME >> {t_time:.6f}")
print(f"MANILA >>  {dt_manila:.6f}")

# UTC >>     1752696711.543170
# LOCAL >>   1752696711.543166
# TIME_TIME >> 1752696711.543163
# MANILA >>  1752696711.543262
