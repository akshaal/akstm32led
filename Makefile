TARGET		= akstm32le
PREFIX		= arm-none-eabi
MCPU=cortex-m3

SRCS		= main.c

# Compiler flags
CFLAGS     = -Wall -g -std=c99 -Os
CFLAGS    += -mlittle-endian -mcpu=${MCPU} -mthumb
CFLAGS    += -ffunction-sections -fdata-sections

# Applications
AR			= $(PREFIX)-ar
CC			= $(PREFIX)-gcc
GDB		= $(PREFIX)-gdbd
OBJCOPY	= $(PREFIX)-objcopy
OBJDUMP	= $(PREFIX)-objdump
SIZE		= $(PREFIX)-size

OBJS		= $(addprefix tmp/,$(SRCS:.c=.o))

all: bin/$(TARGET).bin

bin/$(TARGET).bin: $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -o tmp/$(TARGET).elf
	$(OBJDUMP) -St tmp/$(TARGET).elf >tmp/$(TARGET).lst
	$(SIZE) $(TARGET).elf
	$(OBJCOPY) -O binary tmp/$(TARGET).elf bin/$(TARGET).bin

tmp/%.o : src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
