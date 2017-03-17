// GNU GPL blah blah blah (C) Akshaal, 2017 blah blah blah

#include "FreeRTOS.h"
#include "task.h"
#include "portable.h"
#include "string.h"

#include "ak_rtos.h"
#include "ak_led_fatal_ind.h"

char * ak_strdup(char const * const s) {
    char *dst = ak_malloc(strlen(s) + 1);
    strcpy(dst, s);
    return dst;
}

char *ak_strndup(char const * const s, size_t const size) {
    char *dst = ak_malloc(size  + 1);
    strncpy(dst, s, size);
    *(dst+size) = '\0';
    return dst;
}

void *ak_malloc(size_t const size) {
    void * const rc = pvPortMalloc(size);
    if (rc == NULL) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_malloc);
    }
    return rc;
}

void ak_free(void const * const pv) {
    vPortFree((void*)pv);
}

ak_task_handle ak_task_create(char const * const name, ak_task_f const f, ak_task_priority const prio) {
    TaskHandle_t task_handle;

    if (xTaskCreate(/* function */          f,
                    /* name */              name,
                    /* stack size */        128,
                    /* argument */          NULL,
                    /* priority */          prio,
                    /* task handle PTR */   &task_handle) != pdPASS) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_task_create);
    }

    return task_handle;
}

void ak_task_delay(uint32_t const millisec) {
    TickType_t const ticks = millisec / portTICK_PERIOD_MS;
    vTaskDelay(ticks ? ticks : 1);
}

ak_task_handle ak_queue_create(int const items, size_t const item_size) {
    ak_task_handle const qh = xQueueCreate(items, item_size);

    if (qh == NULL) {
        ak_led_fatal_ind_loop(ak_led_fatal_pattern_queue_create);
    }

    return qh;
}
