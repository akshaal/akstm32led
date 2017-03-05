#include "FreeRTOS.h"
#include "task.h"

void dummyFunction(void) __attribute__((used));

// Never called.
__attribute__((used))
void dummyFunction(void) {
    vTaskSwitchContext();
}
