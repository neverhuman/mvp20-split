#define _GNU_SOURCE
#include <time.h>
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>

static int (*real_clock_gettime)(clockid_t, struct timespec *) = NULL;
static long long base_ms = -1;
static struct timespec start_mono;
static int started = 0;

static long long ts_to_ms(struct timespec *t) {
    return (long long)t->tv_sec * 1000LL + t->tv_nsec / 1000000LL;
}

int clock_gettime(clockid_t clk_id, struct timespec *tp) {
    if (!real_clock_gettime) {
        real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    }
    if (clk_id == CLOCK_REALTIME) {
        if (base_ms < 0) {
            const char *b = getenv("FAKETIME_BASE_MS");
            base_ms = b ? atoll(b) : 1800000000000LL;
        }
        struct timespec mono;
        real_clock_gettime(CLOCK_MONOTONIC, &mono);
        if (!started) {
            start_mono = mono;
            started = 1;
        }
        long long elapsed_ms = ts_to_ms(&mono) - ts_to_ms(&start_mono);
        long long ms = base_ms + elapsed_ms;
        tp->tv_sec = (time_t)(ms / 1000);
        tp->tv_nsec = (long)((ms % 1000) * 1000000LL);
        return 0;
    }
    return real_clock_gettime(clk_id, tp);
}
