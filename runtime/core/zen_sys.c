#include "../bootstrap_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <math.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#ifdef __linux__
#include <sys/ioctl.h>
#endif

extern char **environ;

ZenValue z_stdout;
ZenValue z_stderr;
ZenValue z_stdin;
ZenValue z_args;
ZenValue z_env;

static ZenValue zen_stream_method_write(void* self_ptr, ZenValue args) {
    ZenValue val = (args.type == ZEN_LIST && args.as.list && args.as.list->count > 0) ? args.as.list->items[0] : ZEN_NOTHING_VAL;
    ZenValue self = ZenValue_from_map((struct ZenMap*)self_ptr);
    ZenValue name_val = ZenMap_get_value_at_key(self, ZenValue_make_string("name"));
    if (name_val.type == ZEN_STRING && name_val.as.string && strcmp(name_val.as.string, "stderr") == 0) {
        return ZenIO_write_stderr(val);
    }
    return ZenIO_write_value(val);
}

static ZenValue zen_stream_method_writeln(void* self_ptr, ZenValue args) {
    ZenValue val = (args.type == ZEN_LIST && args.as.list && args.as.list->count > 0) ? args.as.list->items[0] : ZenValue_make_string("");
    ZenValue self = ZenValue_from_map((struct ZenMap*)self_ptr);
    ZenValue name_val = ZenMap_get_value_at_key(self, ZenValue_make_string("name"));
    if (name_val.type == ZEN_STRING && name_val.as.string && strcmp(name_val.as.string, "stderr") == 0) {
        return ZenIO_write_line_stderr(val);
    }
    return ZenIO_write_line(val);
}

static ZenValue zen_stream_method_flush(void* self_ptr, ZenValue args) {
    ZenValue self = ZenValue_from_map((struct ZenMap*)self_ptr);
    ZenValue name_val = ZenMap_get_value_at_key(self, ZenValue_make_string("name"));
    if (name_val.type == ZEN_STRING && name_val.as.string && strcmp(name_val.as.string, "stderr") == 0) {
        return ZenIO_flush_stderr();
    }
    return ZenIO_flush();
}

static ZenValue zen_stream_method_read(void* self_ptr, ZenValue args) {
    ZenValue prompt = (args.type == ZEN_LIST && args.as.list && args.as.list->count > 0) ? args.as.list->items[0] : ZEN_NOTHING_VAL;
    return ZenIO_read_value(prompt);
}

static ZenValue zen_stream_method_readln(void* self_ptr, ZenValue args) {
    ZenValue prompt = (args.type == ZEN_LIST && args.as.list && args.as.list->count > 0) ? args.as.list->items[0] : ZEN_NOTHING_VAL;
    return ZenIO_read_value(prompt);
}

static ZenValue zen_stream_method_lines(void* self_ptr, ZenValue args) {
    (void)self_ptr;
    (void)args;
    return ZenIO_stdin_lines();
}

void ZenRuntime_initialize(void) {
    __builtin_output = ZenValue_make_nothing();
    __builtin_input = ZenValue_make_nothing();
    __builtin_file = ZenValue_make_nothing();
    __builtin_sys = ZenValue_make_nothing();
    __builtin_string = ZenValue_make_nothing();
    __builtin_math = ZenValue_make_nothing();
    __builtin_list = ZenValue_make_nothing();
    __builtin_map = ZenValue_make_nothing();
    __builtin_set = ZenValue_make_nothing();
    __builtin_range = ZenValue_make_nothing();
    __builtin_time = ZenValue_make_nothing();
    __builtin_term = ZenValue_make_nothing();
    module = ZenValue_make_nothing();
    ZenReflect_runtime_init();

    // Stream methods
    ZenReflect_register_method("Stream", "write", zen_stream_method_write);
    ZenReflect_register_method("Stream", "writeln", zen_stream_method_writeln);
    ZenReflect_register_method("Stream", "write_line", zen_stream_method_writeln);
    ZenReflect_register_method("Stream", "flush", zen_stream_method_flush);
    ZenReflect_register_method("Stream", "read", zen_stream_method_read);
    ZenReflect_register_method("Stream", "readln", zen_stream_method_readln);
    ZenReflect_register_method("Stream", "read_line", zen_stream_method_readln);
    ZenReflect_register_method("Stream", "lines", zen_stream_method_lines);

    // Ambient streams
    z_stdout = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(z_stdout, ZenValue_make_string("__type"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stdout, ZenValue_make_string("kind"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stdout, ZenValue_make_string("name"), ZenValue_make_string("stdout"));
    ZenMap_set_value_at_key(z_stdout, ZenValue_make_string("fd"), ZenValue_make_integer(1));
    ZenReflect_tag_object(z_stdout.as.map, "Stream");

    z_stderr = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(z_stderr, ZenValue_make_string("__type"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stderr, ZenValue_make_string("kind"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stderr, ZenValue_make_string("name"), ZenValue_make_string("stderr"));
    ZenMap_set_value_at_key(z_stderr, ZenValue_make_string("fd"), ZenValue_make_integer(2));
    ZenReflect_tag_object(z_stderr.as.map, "Stream");

    z_stdin = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(z_stdin, ZenValue_make_string("__type"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stdin, ZenValue_make_string("kind"), ZenValue_make_string("Stream"));
    ZenMap_set_value_at_key(z_stdin, ZenValue_make_string("name"), ZenValue_make_string("stdin"));
    ZenMap_set_value_at_key(z_stdin, ZenValue_make_string("fd"), ZenValue_make_integer(0));
    ZenReflect_tag_object(z_stdin.as.map, "Stream");

    z_args = ZenValue_from_list(ZenList_new());

    z_env = ZenMap_make_from_arguments(0);
    if (environ) {
        for (char **e = environ; *e != NULL; e++) {
            char* eq = strchr(*e, '=');
            if (eq) {
                size_t klen = (size_t)(eq - *e);
                char kbuf[256];
                if (klen < sizeof(kbuf)) {
                    memcpy(kbuf, *e, klen);
                    kbuf[klen] = '\0';
                    ZenMap_set_value_at_key(z_env, ZenValue_make_string(kbuf), ZenValue_make_string(eq + 1));
                }
            }
        }
    }

    ZenTask_scheduler_init();
}

static struct ZenList* ZenSystem_global_arguments = NULL;

/* Global module context (see ZenModule_initialize). Default empty until init. */
ZenValue module;

void ZenModule_initialize(const char* name, const char* path,
                          const char* file, const char* dir, int is_entry) {
    module = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(module, ZenValue_make_string("name"),
                            ZenValue_make_string(name ? name : ""));
    ZenMap_set_value_at_key(module, ZenValue_make_string("path"),
                            ZenValue_make_string(path ? path : ""));
    ZenMap_set_value_at_key(module, ZenValue_make_string("file"),
                            ZenValue_make_string(file ? file : ""));
    ZenMap_set_value_at_key(module, ZenValue_make_string("dir"),
                            ZenValue_make_string(dir ? dir : ""));
    ZenMap_set_value_at_key(module, ZenValue_make_string("is_entry"),
                            ZenValue_make_boolean(is_entry ? true : false));
    ZenMap_set_value_at_key(module, ZenValue_make_string("args"), z_args);
}

void ZenSystem_initialize_arguments(int argc, char** argv) {
    ZenSystem_global_arguments = ZenList_new();
    for (int i = 0; i < argc; i++) {
        ZenList_append_value(ZenValue_from_list(ZenSystem_global_arguments), ZenValue_make_string(argv[i]));
    }
    z_args = ZenValue_from_list(ZenSystem_global_arguments);
    if (module.type == ZEN_MAP) {
        ZenMap_set_value_at_key(module, ZenValue_make_string("args"), z_args);
    }
}

ZenValue ZenSystem_get_args(void) {
    if (!ZenSystem_global_arguments) return ZenValue_from_list(ZenList_new());
    return ZenValue_from_list(ZenSystem_global_arguments);
}

ZenValue ZenSystem_exit(ZenValue code_value) {
    int code = (int)code_value.as.integer;
    exit(code);
    return ZenValue_make_nothing();
}

ZenValue ZenSystem_get_env(ZenValue name_value) {
    const char* name = ZenString_get_pointer(name_value);
    if (!name) return ZenValue_make_nothing();
    char* val = getenv(name);
    return val ? ZenValue_make_string(val) : ZenValue_make_nothing();
}

ZenValue ZenSystem_set_env(ZenValue name_value, ZenValue val_value) {
    const char* name = ZenString_get_pointer(name_value);
    if (!name) return ZenValue_make_boolean(false);
    const char* val = ZenString_get_pointer(val_value);
    if (val) {
        setenv(name, val, 1);
    } else {
        unsetenv(name);
    }
    return ZenValue_make_boolean(true);
}

ZenValue ZenSystem_unset_env(ZenValue name_value) {
    const char* name = ZenString_get_pointer(name_value);
    if (!name) return ZenValue_make_boolean(false);
    unsetenv(name);
    return ZenValue_make_boolean(true);
}

ZenValue ZenSystem_get_env_map(void) {
    return z_env;
}

ZenValue ZenSystem_get_cwd(void) {
    char buf[1024];
    if (getcwd(buf, sizeof(buf))) return ZenValue_make_string(buf);
    return ZenValue_make_string("");
}

ZenValue ZenSystem_chdir(ZenValue path_val) {
    const char* path = ZenString_get_pointer(path_val);
    if (!path) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(chdir(path) == 0);
}

ZenValue ZenSystem_platform(void) {
    #ifdef _WIN32
    return ZenValue_make_string("windows");
    #elif __APPLE__
    return ZenValue_make_string("macos");
    #else
    return ZenValue_make_string("linux");
    #endif
}

ZenValue ZenSystem_version(void) {
    return ZenValue_make_string("0.1.0");
}

ZenValue ZenSystem_exec(ZenValue cmd_value) {
    const char* cmd = ZenString_get_pointer(cmd_value);
    if (!cmd) return ZenValue_make_integer(-1);
    int res = system(cmd);
    return ZenValue_make_integer(res);
}

ZenValue ZenValue_make_error_message(ZenValue message) {
    // Match interpreter: __builtin.error(msg) raises a catchable error.
    ZenValue err = ZenValue_make_error(message);
    ZenException_raise(err);
    return err; /* unreachable if raise longjmps */
}

ZenValue ZenValue_make_error_literal(ZenValue message) {
    // Literal constructors return an Error value without raising.
    return ZenValue_make_error(message);
}

static int zen_range_as_codepoint(ZenValue v, long long* out) {
    if (v.type == ZEN_INTEGER) {
        *out = v.as.integer;
        return 1; // integer mode
    }
    if (v.type == ZEN_STRING && v.as.string) {
        // Single UTF-8 code unit for ASCII ranges (a..z); multi-byte later.
        unsigned char c = (unsigned char)v.as.string[0];
        if (v.as.string[0] != '\0' && v.as.string[1] == '\0') {
            *out = (long long)c;
            return 2; // char mode
        }
    }
    return 0;
}

static ZenValue zen_range_build(ZenValue start, ZenValue end, int inclusive, int open_start) {
    long long s = 0, e = 0;
    int sm = zen_range_as_codepoint(start, &s);
    int em = zen_range_as_codepoint(end, &e);
    if (!sm || !em || sm != em) {
        return ZenValue_from_list(ZenList_new());
    }
    int as_char = (sm == 2);

    struct ZenList* list = ZenList_new();
    ZenValue list_v = ZenValue_from_list(list);

    if (s <= e) {
        long long begin = open_start ? (s + 1) : s;
        long long stop = inclusive ? (e + 1) : e;
        for (long long i = begin; i < stop; i++) {
            if (as_char) {
                char buf[2] = { (char)i, 0 };
                ZenList_append_value(list_v, ZenValue_make_string(buf));
            } else {
                ZenList_append_value(list_v, ZenValue_make_integer(i));
            }
        }
    } else {
        long long begin = open_start ? (s - 1) : s;
        long long stop = inclusive ? (e - 1) : e;
        for (long long i = begin; i > stop; i--) {
            if (as_char) {
                char buf[2] = { (char)i, 0 };
                ZenList_append_value(list_v, ZenValue_make_string(buf));
            } else {
                ZenList_append_value(list_v, ZenValue_make_integer(i));
            }
        }
    }
    return list_v;
}

// 4-Range Boundary System (SPEC 6.4):
// Range Between a..b → (a, b) [open interval: both endpoints excluded]
ZenValue ZenValue_range_between(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 0, 1);
}

// Range Inclusive End a..+b → (a, b] [open start, inclusive end]
ZenValue ZenValue_range_open_start_inclusive(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 1, 1);
}

// Range Exclusive End a..-b → [a, b) [closed start, exclusive end]
ZenValue ZenValue_range_exclusive_end(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 0, 0);
}

ZenValue ZenValue_range(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 0, 0);
}

// Range Full Inclusive a...b → [a, b] [closed interval: both endpoints included]
ZenValue ZenValue_range_inclusive(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 1, 0);
}

ZenValue ZenValue_range_full_inclusive(ZenValue start, ZenValue end) {
    return zen_range_build(start, end, 1, 0);
}

// Back-compat alias used by older generated code / builtins.
ZenValue ZenRange_make(ZenValue start, ZenValue end) {
    return ZenValue_range_exclusive_end(start, end);
}

/* ---- Time ---- */

static double zen_time_as_seconds(ZenValue v) {
    if (v.type == ZEN_INTEGER) return (double)v.as.integer;
    if (v.type == ZEN_DECIMAL) return v.as.decimal;
    return 0.0;
}

ZenValue ZenTime_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ZenValue_make_decimal((double)ts.tv_sec + (double)ts.tv_nsec / 1e9);
}

ZenValue ZenTime_wallclock(void) {
    return ZenTime_now();
}

ZenValue ZenTime_monotonic(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ZenValue_make_decimal((double)ts.tv_sec + (double)ts.tv_nsec / 1e9);
}

ZenValue ZenTime_sleep(ZenValue seconds) {
    double s = zen_time_as_seconds(seconds);
    if (s < 0) s = 0;
    struct timespec ts;
    ts.tv_sec = (time_t)s;
    ts.tv_nsec = (long)((s - (double)ts.tv_sec) * 1e9);
    nanosleep(&ts, NULL);
    return ZenValue_make_nothing();
}

/* ---- Terminal (minimal ANSI) ---- */

ZenValue ZenTerm_clear(void) {
    fputs("\033[2J\033[H", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_move(ZenValue x, ZenValue y) {
    long long col = (x.type == ZEN_INTEGER) ? x.as.integer : (long long)x.as.decimal;
    long long row = (y.type == ZEN_INTEGER) ? y.as.integer : (long long)y.as.decimal;
    /* No per-call flush — canvas/render batches then ZenTerm_flush. */
    printf("\033[%lld;%lldH", row, col);
    return ZenValue_make_nothing();
}

static int zen_term_color_code(const char* name) {
    if (!name) return -1;
    if (strcmp(name, "black") == 0) return 0;
    if (strcmp(name, "red") == 0) return 1;
    if (strcmp(name, "green") == 0) return 2;
    if (strcmp(name, "yellow") == 0) return 3;
    if (strcmp(name, "blue") == 0) return 4;
    if (strcmp(name, "magenta") == 0) return 5;
    if (strcmp(name, "cyan") == 0) return 6;
    if (strcmp(name, "white") == 0) return 7;
    return -1;
}

ZenValue ZenTerm_color(ZenValue fg, ZenValue bg) {
    const char* fgs = ZenString_get_pointer(fg);
    const char* bgs = ZenString_get_pointer(bg);
    int fc = zen_term_color_code(fgs);
    int bc = zen_term_color_code(bgs);
    /* Support bright_* as bold + base color (common TUI palette). */
    int bold = 0;
    if (fc < 0 && fgs && strncmp(fgs, "bright_", 7) == 0) {
        bold = 1;
        fc = zen_term_color_code(fgs + 7);
    }
    if (bc < 0 && bgs && strncmp(bgs, "bright_", 7) == 0) {
        bc = zen_term_color_code(bgs + 7);
    }
    if (bold && fc >= 0) printf("\033[1;3%dm", fc);
    else if (fc >= 0) printf("\033[3%dm", fc);
    if (bc >= 0) printf("\033[4%dm", bc);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_reset(void) {
    fputs("\033[0m", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_get_size(void) {
    long long width = 80, height = 24;
#ifdef TIOCGWINSZ
    struct winsize ws;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0) {
        if (ws.ws_col > 0) width = ws.ws_col;
        if (ws.ws_row > 0) height = ws.ws_row;
    }
#endif
    struct ZenMap* m = ZenMap_new();
    ZenValue mv = ZenValue_from_map(m);
    ZenMap_set_value_at_key(mv, ZenValue_make_string("width"), ZenValue_make_integer(width));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("height"), ZenValue_make_integer(height));
    return mv;
}

ZenValue ZenTerm_alt_screen_enter(void) {
    fputs("\033[?1049h", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_alt_screen_exit(void) {
    fputs("\033[?1049l", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

/* ---- Terminal raw mode + keyboard (editor support) ---- */

static struct termios zen_term_saved_tio;
static int zen_term_raw_active = 0;
static int zen_term_saved_valid = 0;
static volatile sig_atomic_t zen_term_resized = 0;

static void zen_term_on_winch(int sig) {
    (void)sig;
    zen_term_resized = 1;
}

static void zen_term_restore_now(void) {
    if (zen_term_raw_active && zen_term_saved_valid && isatty(STDIN_FILENO)) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &zen_term_saved_tio);
        zen_term_raw_active = 0;
    }
    /* Always try to restore display basics */
    fputs("\033[?25h\033[0m\033[?1049l", stdout);
    fflush(stdout);
}

static void zen_term_atexit_restore(void) {
    zen_term_restore_now();
}

ZenValue ZenTerm_raw_enter(void) {
    if (!isatty(STDIN_FILENO)) {
        return ZenValue_make_boolean(false);
    }
    if (!zen_term_raw_active) {
        if (tcgetattr(STDIN_FILENO, &zen_term_saved_tio) != 0) {
            return ZenValue_make_boolean(false);
        }
        zen_term_saved_valid = 1;
        struct termios raw = zen_term_saved_tio;
        /* cfmakeraw-like: cbreak + no echo + 8-bit */
        raw.c_iflag &= ~(unsigned)(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
        raw.c_oflag &= ~(unsigned)(OPOST);
        raw.c_cflag |= (unsigned)(CS8);
        raw.c_lflag &= ~(unsigned)(ECHO | ICANON | IEXTEN | ISIG);
        raw.c_cc[VMIN] = 1;
        raw.c_cc[VTIME] = 0;
        if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) != 0) {
            return ZenValue_make_boolean(false);
        }
        zen_term_raw_active = 1;
        atexit(zen_term_atexit_restore);
        signal(SIGWINCH, zen_term_on_winch);
        /* Ensure cleanup on common fatal signals */
        signal(SIGINT, SIG_DFL); /* ISIG off so Ctrl-C is a key; process may still get SIGTERM */
        signal(SIGTERM, SIG_DFL);
    }
    return ZenValue_make_boolean(true);
}

ZenValue ZenTerm_raw_exit(void) {
    zen_term_restore_now();
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_hide_cursor(void) {
    fputs("\033[?25l", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_show_cursor(void) {
    fputs("\033[?25h", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_clear_eol(void) {
    fputs("\033[K", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_write(ZenValue text) {
    const char* s = ZenString_get_pointer(text);
    if (s) fputs(s, stdout);
    return ZenValue_make_nothing();
}

/* Apply fg/bg by name; supports bright_* as bold+base. No flush. */
static void zen_term_apply_color_cstr(const char* fgs, const char* bgs) {
    int fc = zen_term_color_code(fgs);
    int bc = zen_term_color_code(bgs);
    int bold = 0;
    if (fc < 0 && fgs && strncmp(fgs, "bright_", 7) == 0) {
        bold = 1;
        fc = zen_term_color_code(fgs + 7);
    }
    if (bc < 0 && bgs && strncmp(bgs, "bright_", 7) == 0) {
        bc = zen_term_color_code(bgs + 7);
    }
    if (bold && fc >= 0) printf("\033[1;3%dm", fc);
    else if (fc >= 0) printf("\033[3%dm", fc);
    if (bc >= 0) printf("\033[4%dm", bc);
}

static const char* zen_cell_cstr(ZenValue v) {
    if (v.type != ZEN_STRING) return " ";
    const char* s = ZenString_get_pointer(v);
    if (!s || s[0] == '\0') return " ";
    return s;
}

static const char* zen_color_cstr(ZenValue v) {
    if (v.type != ZEN_STRING) return "white";
    const char* s = ZenString_get_pointer(v);
    return s ? s : "white";
}

ZenValue ZenTerm_paint_canvas(ZenValue canvas) {
    if (canvas.type != ZEN_MAP) return ZenValue_make_nothing();

    ZenValue wv = ZenMap_get_value_at_key(canvas, ZenValue_make_string("width"));
    ZenValue hv = ZenMap_get_value_at_key(canvas, ZenValue_make_string("height"));
    ZenValue buffer = ZenMap_get_value_at_key(canvas, ZenValue_make_string("buffer"));
    ZenValue fg_buf = ZenMap_get_value_at_key(canvas, ZenValue_make_string("fg_buffer"));
    ZenValue bg_buf = ZenMap_get_value_at_key(canvas, ZenValue_make_string("bg_buffer"));

    int w = (wv.type == ZEN_INTEGER) ? (int)wv.as.integer : 0;
    int h = (hv.type == ZEN_INTEGER) ? (int)hv.as.integer : 0;
    if (w <= 0 || h <= 0) return ZenValue_make_nothing();
    if (buffer.type != ZEN_LIST || !buffer.as.list) return ZenValue_make_nothing();
    if (fg_buf.type != ZEN_LIST || !fg_buf.as.list) return ZenValue_make_nothing();
    if (bg_buf.type != ZEN_LIST || !bg_buf.as.list) return ZenValue_make_nothing();

    /* Hide cursor during paint is caller's job; we batch writes hard. */
    for (int y = 0; y < h && y < buffer.as.list->count; y++) {
        ZenValue row = buffer.as.list->items[y];
        ZenValue fg_row = (y < fg_buf.as.list->count) ? fg_buf.as.list->items[y] : ZenValue_make_nothing();
        ZenValue bg_row = (y < bg_buf.as.list->count) ? bg_buf.as.list->items[y] : ZenValue_make_nothing();
        if (row.type != ZEN_LIST || !row.as.list) continue;

        printf("\033[%d;1H", y + 1); /* 1-based row, col 1 */

        const char* last_fg = NULL;
        const char* last_bg = NULL;
        int n = row.as.list->count;
        if (n > w) n = w;

        for (int x = 0; x < n; x++) {
            const char* ch = zen_cell_cstr(row.as.list->items[x]);
            const char* fg = "white";
            const char* bg = "black";
            if (fg_row.type == ZEN_LIST && fg_row.as.list && x < fg_row.as.list->count)
                fg = zen_color_cstr(fg_row.as.list->items[x]);
            if (bg_row.type == ZEN_LIST && bg_row.as.list && x < bg_row.as.list->count)
                bg = zen_color_cstr(bg_row.as.list->items[x]);

            if (!last_fg || !last_bg || strcmp(fg, last_fg) != 0 || strcmp(bg, last_bg) != 0) {
                zen_term_apply_color_cstr(fg, bg);
                last_fg = fg;
                last_bg = bg;
            }
            /* Write first UTF-8-ish byte sequence as single char (ASCII TUI). */
            fputc((unsigned char)ch[0], stdout);
        }
    }
    fputs("\033[0m", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_flush(void) {
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_mouse_enable(void) {
    /* X10 + SGR mouse tracking (matches interpret builtin) */
    fputs("\033[?1000h\033[?1006h", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_mouse_disable(void) {
    fputs("\033[?1000l\033[?1006l", stdout);
    fflush(stdout);
    return ZenValue_make_nothing();
}

ZenValue ZenTerm_is_tty(void) {
    return ZenValue_make_boolean(isatty(STDIN_FILENO) ? true : false);
}

static ZenValue zen_term_key_map(const char* kind, const char* name, const char* ch, int ctrl, int code) {
    struct ZenMap* m = ZenMap_new();
    ZenValue mv = ZenValue_from_map(m);
    ZenMap_set_value_at_key(mv, ZenValue_make_string("kind"), ZenValue_make_string(kind ? kind : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("name"), ZenValue_make_string(name ? name : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("ch"), ZenValue_make_string(ch ? ch : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("ctrl"), ZenValue_make_boolean(ctrl ? true : false));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("code"), ZenValue_make_integer(code));
    return mv;
}

static int zen_term_read_byte_timeout(int timeout_ms) {
    struct pollfd pfd;
    pfd.fd = STDIN_FILENO;
    pfd.events = POLLIN;
    int pr = poll(&pfd, 1, timeout_ms);
    if (pr <= 0) return -1;
    unsigned char c = 0;
    ssize_t n = read(STDIN_FILENO, &c, 1);
    if (n != 1) return -1;
    return (int)c;
}

static int zen_term_read_byte_block(void) {
    unsigned char c = 0;
    for (;;) {
        if (zen_term_resized) {
            return -2; /* resize sentinel */
        }
        ssize_t n = read(STDIN_FILENO, &c, 1);
        if (n == 1) return (int)c;
        if (n < 0 && errno == EINTR) continue;
        return -1;
    }
}

static ZenValue zen_term_parse_escape(void) {
    /* After reading ESC, peek for CSI with short timeout */
    int b1 = zen_term_read_byte_timeout(50);
    if (b1 < 0) {
        return zen_term_key_map("special", "escape", "", 0, 27);
    }
    if (b1 == '[') {
        int b2 = zen_term_read_byte_timeout(50);
        if (b2 < 0) return zen_term_key_map("special", "escape", "", 0, 27);
        if (b2 == 'A') return zen_term_key_map("special", "up", "", 0, 0);
        if (b2 == 'B') return zen_term_key_map("special", "down", "", 0, 0);
        if (b2 == 'C') return zen_term_key_map("special", "right", "", 0, 0);
        if (b2 == 'D') return zen_term_key_map("special", "left", "", 0, 0);
        if (b2 == 'H') return zen_term_key_map("special", "home", "", 0, 0);
        if (b2 == 'F') return zen_term_key_map("special", "end", "", 0, 0);
        /* CSI n ~  forms: 1~ home, 3~ delete, 4~ end, 5~ pgup, 6~ pgdn */
        if (b2 >= '0' && b2 <= '9') {
            int num = b2 - '0';
            int b3 = zen_term_read_byte_timeout(50);
            while (b3 >= '0' && b3 <= '9') {
                num = num * 10 + (b3 - '0');
                b3 = zen_term_read_byte_timeout(50);
            }
            if (b3 == '~') {
                if (num == 1 || num == 7) return zen_term_key_map("special", "home", "", 0, 0);
                if (num == 3) return zen_term_key_map("special", "delete", "", 0, 0);
                if (num == 4 || num == 8) return zen_term_key_map("special", "end", "", 0, 0);
                if (num == 5) return zen_term_key_map("special", "pageup", "", 0, 0);
                if (num == 6) return zen_term_key_map("special", "pagedown", "", 0, 0);
            }
            /* CSI 1;5A style — ignore modifiers, map arrow letter if present */
            if (b3 == ';') {
                int b4 = zen_term_read_byte_timeout(50);
                int b5 = zen_term_read_byte_timeout(50);
                (void)b4;
                if (b5 == 'A') return zen_term_key_map("special", "up", "", 0, 0);
                if (b5 == 'B') return zen_term_key_map("special", "down", "", 0, 0);
                if (b5 == 'C') return zen_term_key_map("special", "right", "", 0, 0);
                if (b5 == 'D') return zen_term_key_map("special", "left", "", 0, 0);
            }
        }
        return zen_term_key_map("special", "unknown", "", 0, b2);
    }
    if (b1 == 'O') {
        int b2 = zen_term_read_byte_timeout(50);
        if (b2 == 'H') return zen_term_key_map("special", "home", "", 0, 0);
        if (b2 == 'F') return zen_term_key_map("special", "end", "", 0, 0);
    }
    /* Alt+key often sent as ESC + char */
    if (b1 >= 32 && b1 < 127) {
        char ch[2] = { (char)b1, 0 };
        return zen_term_key_map("char", "", ch, 0, b1); /* treat as char; alt not tracked yet */
    }
    return zen_term_key_map("special", "escape", "", 0, 27);
}

static ZenValue zen_term_key_from_byte(int c) {
    if (c == -2 || zen_term_resized) {
        zen_term_resized = 0;
        return zen_term_key_map("resize", "resize", "", 0, 0);
    }
    if (c < 0) {
        return zen_term_key_map("none", "none", "", 0, 0);
    }
    if (c == 27) return zen_term_parse_escape();
    if (c == 127 || c == 8) return zen_term_key_map("special", "backspace", "", 0, c);
    if (c == 13 || c == 10) return zen_term_key_map("special", "enter", "", 0, c);
    if (c == 9) return zen_term_key_map("special", "tab", "", 0, c);
    if (c >= 1 && c <= 26) {
        /* Ctrl+A .. Ctrl+Z */
        char name[16];
        snprintf(name, sizeof(name), "ctrl_%c", (char)('a' + c - 1));
        return zen_term_key_map("special", name, "", 1, c);
    }
    if (c >= 32 && c < 127) {
        char ch[2] = { (char)c, 0 };
        return zen_term_key_map("char", "", ch, 0, c);
    }
    return zen_term_key_map("special", "unknown", "", 0, c);
}

ZenValue ZenTerm_read_key(void) {
    if (zen_term_resized) {
        zen_term_resized = 0;
        return zen_term_key_map("resize", "resize", "", 0, 0);
    }
    int c = zen_term_read_byte_block();
    return zen_term_key_from_byte(c);
}

ZenValue ZenTerm_poll_key(ZenValue timeout_ms) {
    if (zen_term_resized) {
        zen_term_resized = 0;
        return zen_term_key_map("resize", "resize", "", 0, 0);
    }
    int ms = 0;
    if (timeout_ms.type == ZEN_INTEGER) ms = (int)timeout_ms.as.integer;
    else if (timeout_ms.type == ZEN_DECIMAL) ms = (int)timeout_ms.as.decimal;
    if (ms < 0) ms = 0;
    int c = zen_term_read_byte_timeout(ms);
    if (c < 0) {
        if (zen_term_resized) {
            zen_term_resized = 0;
            return zen_term_key_map("resize", "resize", "", 0, 0);
        }
        return zen_term_key_map("none", "none", "", 0, 0);
    }
    if (c == 27) return zen_term_parse_escape();
    return zen_term_key_from_byte(c);
}

/* ---- Process ---- */

typedef struct ZenProcessHandle {
    FILE* pipe;
    char* stdout_buf;
    size_t stdout_len;
    int code;
    int finished;
    int pid; /* best-effort; often 0 for popen-backed handles */
} ZenProcessHandle;

static char* zen_process_build_cmdline(ZenValue command, ZenValue arguments) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) return NULL;

    /* Rough size estimate */
    size_t cap = strlen(cmd) + 16;
    long long argc = 0;
    if (arguments.type == ZEN_LIST && arguments.as.list) {
        argc = ZenValue_to_integer(ZenList_get_length(arguments));
        for (long long i = 0; i < argc; i++) {
            ZenValue a = ZenList_get_value_at_index(arguments, ZenValue_make_integer(i));
            const char* s = ZenString_get_pointer(a);
            cap += (s ? strlen(s) : 0) + 4;
        }
    }
    char* buf = (char*)malloc(cap);
    if (!buf) return NULL;
    buf[0] = '\0';

    /* Quote command if it contains spaces (minimal safety). */
    if (strchr(cmd, ' ')) {
        snprintf(buf, cap, "\"%s\"", cmd);
    } else {
        snprintf(buf, cap, "%s", cmd);
    }

    if (arguments.type == ZEN_LIST && arguments.as.list) {
        for (long long i = 0; i < argc; i++) {
            ZenValue a = ZenList_get_value_at_index(arguments, ZenValue_make_integer(i));
            const char* s = ZenString_get_pointer(a);
            if (!s) s = "";
            size_t used = strlen(buf);
            /* Prefer simple shell-safe quoting for args without quotes. */
            if (strchr(s, '\'') == NULL) {
                snprintf(buf + used, cap - used, " '%s'", s);
            } else {
                snprintf(buf + used, cap - used, " %s", s);
            }
        }
    }
    return buf;
}

static char* zen_process_read_all(FILE* f, size_t* out_len) {
    size_t cap = 4096, len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) {
        if (out_len) *out_len = 0;
        return NULL;
    }
    while (f && !feof(f)) {
        if (len + 1024 >= cap) {
            cap *= 2;
            char* nb = (char*)realloc(buf, cap);
            if (!nb) break;
            buf = nb;
        }
        size_t n = fread(buf + len, 1, 1024, f);
        if (n == 0) break;
        len += n;
    }
    buf[len] = '\0';
    if (out_len) *out_len = len;
    return buf;
}

ZenValue ZenProcess_run(ZenValue command, ZenValue arguments) {
    char* cmdline = zen_process_build_cmdline(command, arguments);
    if (!cmdline) return ZenValue_make_string("");
    FILE* f = popen(cmdline, "r");
    free(cmdline);
    if (!f) return ZenValue_make_string("");
    size_t len = 0;
    char* out = zen_process_read_all(f, &len);
    int st = pclose(f);
    (void)st;
    if (!out) return ZenValue_make_string("");
    ZenValue z = ZenValue_make_string(out);
    free(out);
    return z;
}

ZenValue ZenProcess_get_id(void) {
    return ZenValue_make_integer((long long)getpid());
}

ZenValue ZenProcess_spawn(ZenValue command, ZenValue arguments) {
    char* cmdline = zen_process_build_cmdline(command, arguments);
    if (!cmdline) return ZenValue_make_nothing();
    FILE* f = popen(cmdline, "r");
    free(cmdline);
    if (!f) return ZenValue_make_nothing();
    ZenProcessHandle* h = (ZenProcessHandle*)calloc(1, sizeof(ZenProcessHandle));
    if (!h) {
        pclose(f);
        return ZenValue_make_nothing();
    }
    h->pipe = f;
    h->code = -1;
    h->finished = 0;
    h->pid = 0;
    h->stdout_buf = NULL;
    h->stdout_len = 0;
    return ZenValue_from_object(h);
}

static ZenProcessHandle* zen_process_from_ptr(void* self) {
    if (!self) return NULL;
    ZenValue* as_val = (ZenValue*)self;
    if (as_val->type == ZEN_OBJECT && as_val->as.object) {
        return (ZenProcessHandle*)as_val->as.object;
    }
    return (ZenProcessHandle*)self;
}

ZenValue ZenObject_wait(void* self) {
    ZenProcessHandle* h = zen_process_from_ptr(self);
    if (!h) return ZenValue_make_integer(-1);
    if (!h->finished) {
        if (h->pipe) {
            size_t len = 0;
            char* out = zen_process_read_all(h->pipe, &len);
            h->stdout_buf = out;
            h->stdout_len = len;
            int st = pclose(h->pipe);
            h->pipe = NULL;
#if defined(WIFEXITED) && defined(WEXITSTATUS)
            if (WIFEXITED(st)) h->code = WEXITSTATUS(st);
            else h->code = st;
#else
            h->code = st;
#endif
        }
        h->finished = 1;
    }
    return ZenValue_make_integer(h->code);
}

ZenValue ZenObject_get_stdout(void* self) {
    ZenProcessHandle* h = zen_process_from_ptr(self);
    if (!h) return ZenValue_make_string("");
    if (!h->finished) {
        /* Drain pipe if caller asks for stdout before wait. */
        (void)ZenObject_wait(self);
    }
    if (!h->stdout_buf) return ZenValue_make_string("");
    return ZenValue_make_string(h->stdout_buf);
}

ZenValue ZenObject_get_code(void* self) {
    ZenProcessHandle* h = zen_process_from_ptr(self);
    if (!h) return ZenValue_make_integer(-1);
    if (!h->finished) (void)ZenObject_wait(self);
    return ZenValue_make_integer(h->code);
}

ZenValue ZenObject_kill(void* self) {
    ZenProcessHandle* h = zen_process_from_ptr(self);
    if (!h) return ZenValue_make_nothing();
    if (h->pipe) {
        /* Best-effort: close the pipe (child may become orphan until reaped). */
        pclose(h->pipe);
        h->pipe = NULL;
        h->finished = 1;
        h->code = -1;
    }
    return ZenValue_make_nothing();
}

/* ---- Shell scripting (/bin/sh -c) ---- */

static int zen_read_fd_all(int fd, char** out_buf, size_t* out_len) {
    size_t cap = 4096, len = 0;
    char* buf = (char*)malloc(cap);
    if (!buf) {
        if (out_buf) *out_buf = NULL;
        if (out_len) *out_len = 0;
        return -1;
    }
    for (;;) {
        if (len + 1024 >= cap) {
            cap *= 2;
            char* nb = (char*)realloc(buf, cap);
            if (!nb) break;
            buf = nb;
        }
        ssize_t n = read(fd, buf + len, 1024);
        if (n < 0) break;
        if (n == 0) break;
        len += (size_t)n;
    }
    buf[len] = '\0';
    if (out_buf) *out_buf = buf;
    else free(buf);
    if (out_len) *out_len = len;
    return 0;
}

/* Apply string→string entries from env map onto the child environment. */
static void zen_apply_env_map(ZenValue env_map) {
    if (env_map.type != ZEN_MAP || !env_map.as.map) return;
    struct ZenMap* m = env_map.as.map;
    for (int i = 0; i < m->count; i++) {
        ZenValue key = m->entries[i].key;
        ZenValue val = m->entries[i].value;
        const char* k = ZenString_get_pointer(key);
        if (!k || k[0] == '\0') continue;
        const char* v = ZenString_get_pointer(val);
        if (!v) {
            /* Non-string values: stringify integers/bools lightly */
            if (val.type == ZEN_INTEGER) {
                char buf[64];
                snprintf(buf, sizeof(buf), "%lld", (long long)val.as.integer);
                setenv(k, buf, 1);
                continue;
            }
            v = "";
        }
        setenv(k, v, 1);
    }
}

static ZenValue zen_shell_result_impl(const char* cmd, int capture_stderr_separate, const char* cwd, ZenValue env_map) {
    int out_pipe[2] = {-1, -1};
    int err_pipe[2] = {-1, -1};
    if (pipe(out_pipe) != 0) {
        return ZenValue_make_nothing();
    }
    if (capture_stderr_separate && pipe(err_pipe) != 0) {
        close(out_pipe[0]);
        close(out_pipe[1]);
        return ZenValue_make_nothing();
    }

    pid_t pid = fork();
    if (pid < 0) {
        close(out_pipe[0]); close(out_pipe[1]);
        if (capture_stderr_separate) { close(err_pipe[0]); close(err_pipe[1]); }
        return ZenValue_make_nothing();
    }

    if (pid == 0) {
        /* Child — optional cwd + env (does not affect parent process). */
        if (cwd && cwd[0] != '\0') {
            if (chdir(cwd) != 0) {
                _exit(126);
            }
        }
        zen_apply_env_map(env_map);
        close(out_pipe[0]);
        dup2(out_pipe[1], STDOUT_FILENO);
        close(out_pipe[1]);
        if (capture_stderr_separate) {
            close(err_pipe[0]);
            dup2(err_pipe[1], STDERR_FILENO);
            close(err_pipe[1]);
        } else {
            dup2(STDOUT_FILENO, STDERR_FILENO);
        }
        execl("/bin/sh", "sh", "-c", cmd ? cmd : "", (char*)NULL);
        _exit(127);
    }

    /* Parent */
    close(out_pipe[1]);
    if (capture_stderr_separate) close(err_pipe[1]);

    char* out = NULL;
    char* err = NULL;
    size_t out_len = 0, err_len = 0;
    zen_read_fd_all(out_pipe[0], &out, &out_len);
    close(out_pipe[0]);
    if (capture_stderr_separate) {
        zen_read_fd_all(err_pipe[0], &err, &err_len);
        close(err_pipe[0]);
    }

    int status = 0;
    waitpid(pid, &status, 0);
    int code = 127;
    if (WIFEXITED(status)) code = WEXITSTATUS(status);
    else if (WIFSIGNALED(status)) code = 128 + WTERMSIG(status);

    if (!capture_stderr_separate) {
        /* shell(): return stdout (+ merged stderr) as string */
        ZenValue z = ZenValue_make_string(out ? out : "");
        free(out);
        free(err);
        return z;
    }

    struct ZenMap* m = ZenMap_new();
    ZenValue mv = ZenValue_from_map(m);
    ZenMap_set_value_at_key(mv, ZenValue_make_string("stdout"), ZenValue_make_string(out ? out : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("stderr"), ZenValue_make_string(err ? err : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("code"), ZenValue_make_integer(code));
    free(out);
    free(err);
    return mv;
}

static ZenValue zen_env_none(void) {
    return ZenValue_make_nothing();
}

ZenValue ZenProcess_shell(ZenValue command) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 0, NULL, zen_env_none());
}

ZenValue ZenProcess_shell_result(ZenValue command) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 1, NULL, zen_env_none());
}

ZenValue ZenProcess_shell_in(ZenValue cwd_val, ZenValue command) {
    const char* cwd = ZenString_get_pointer(cwd_val);
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 0, cwd, zen_env_none());
}

ZenValue ZenProcess_shell_result_in(ZenValue cwd_val, ZenValue command) {
    const char* cwd = ZenString_get_pointer(cwd_val);
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 1, cwd, zen_env_none());
}

ZenValue ZenProcess_shell_env(ZenValue env, ZenValue command) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 0, NULL, env);
}

ZenValue ZenProcess_shell_result_env(ZenValue env, ZenValue command) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 1, NULL, env);
}

ZenValue ZenProcess_shell_in_env(ZenValue cwd_val, ZenValue env, ZenValue command) {
    const char* cwd = ZenString_get_pointer(cwd_val);
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 0, cwd, env);
}

ZenValue ZenProcess_shell_result_in_env(ZenValue cwd_val, ZenValue env, ZenValue command) {
    const char* cwd = ZenString_get_pointer(cwd_val);
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_result_impl(cmd, 1, cwd, env);
}

/* ---- Real pipe(2) argv pipeline ---- */

#define ZEN_PIPE_MAX_STAGES 32
#define ZEN_PIPE_MAX_ARGS 64

static int zen_stage_to_argv(ZenValue stage, char** argv, int max_args) {
    if (stage.type != ZEN_LIST || !stage.as.list) return -1;
    int n = stage.as.list->count;
    if (n <= 0 || n >= max_args) return -1;
    for (int i = 0; i < n; i++) {
        ZenValue a = stage.as.list->items[i];
        const char* s = ZenString_get_pointer(a);
        if (!s) s = "";
        argv[i] = (char*)s; /* strings owned by ZenValue heap; live for exec lifetime */
    }
    argv[n] = NULL;
    return n;
}

ZenValue ZenProcess_pipeline_run(ZenValue stages, ZenValue cwd_val, ZenValue env) {
    if (stages.type != ZEN_LIST || !stages.as.list || stages.as.list->count <= 0) {
        struct ZenMap* m = ZenMap_new();
        ZenValue mv = ZenValue_from_map(m);
        ZenMap_set_value_at_key(mv, ZenValue_make_string("stdout"), ZenValue_make_string(""));
        ZenMap_set_value_at_key(mv, ZenValue_make_string("stderr"), ZenValue_make_string(""));
        ZenMap_set_value_at_key(mv, ZenValue_make_string("code"), ZenValue_make_integer(0));
        return mv;
    }

    int n = stages.as.list->count;
    if (n > ZEN_PIPE_MAX_STAGES) n = ZEN_PIPE_MAX_STAGES;

    const char* cwd = ZenString_get_pointer(cwd_val);

    /* pipes between stages: n-1; plus capture for last stdout and last stderr */
    int mid_pipes[ZEN_PIPE_MAX_STAGES][2];
    int out_cap[2] = {-1, -1};
    int err_cap[2] = {-1, -1};
    for (int i = 0; i < n - 1; i++) {
        if (pipe(mid_pipes[i]) != 0) {
            return ZenValue_make_nothing();
        }
    }
    if (pipe(out_cap) != 0 || pipe(err_cap) != 0) {
        return ZenValue_make_nothing();
    }

    pid_t pids[ZEN_PIPE_MAX_STAGES];
    for (int i = 0; i < n; i++) pids[i] = -1;

    for (int i = 0; i < n; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            /* best-effort cleanup */
            for (int k = 0; k < n - 1; k++) {
                close(mid_pipes[k][0]); close(mid_pipes[k][1]);
            }
            close(out_cap[0]); close(out_cap[1]);
            close(err_cap[0]); close(err_cap[1]);
            return ZenValue_make_nothing();
        }
        if (pid == 0) {
            /* Child i */
            if (cwd && cwd[0] != '\0') {
                if (chdir(cwd) != 0) _exit(126);
            }
            zen_apply_env_map(env);

            /* stdin */
            if (i == 0) {
                int devnull = open("/dev/null", O_RDONLY);
                if (devnull >= 0) {
                    dup2(devnull, STDIN_FILENO);
                    close(devnull);
                }
            } else {
                dup2(mid_pipes[i - 1][0], STDIN_FILENO);
            }
            /* stdout */
            if (i == n - 1) {
                dup2(out_cap[1], STDOUT_FILENO);
            } else {
                dup2(mid_pipes[i][1], STDOUT_FILENO);
            }
            /* stderr → capture only from last stage; others inherit then closed */
            if (i == n - 1) {
                dup2(err_cap[1], STDERR_FILENO);
            }

            /* close all pipe fds in child */
            for (int k = 0; k < n - 1; k++) {
                close(mid_pipes[k][0]);
                close(mid_pipes[k][1]);
            }
            close(out_cap[0]); close(out_cap[1]);
            close(err_cap[0]); close(err_cap[1]);

            char* argv[ZEN_PIPE_MAX_ARGS];
            ZenValue stage = stages.as.list->items[i];
            if (zen_stage_to_argv(stage, argv, ZEN_PIPE_MAX_ARGS) < 1) {
                _exit(127);
            }
            execvp(argv[0], argv);
            _exit(127);
        }
        pids[i] = pid;
    }

    /* Parent: close write ends we don't need */
    for (int k = 0; k < n - 1; k++) {
        close(mid_pipes[k][0]);
        close(mid_pipes[k][1]);
    }
    close(out_cap[1]);
    close(err_cap[1]);

    char* out = NULL;
    char* err = NULL;
    size_t out_len = 0, err_len = 0;
    zen_read_fd_all(out_cap[0], &out, &out_len);
    zen_read_fd_all(err_cap[0], &err, &err_len);
    close(out_cap[0]);
    close(err_cap[0]);

    int last_code = 0;
    for (int i = 0; i < n; i++) {
        int status = 0;
        if (pids[i] > 0) {
            waitpid(pids[i], &status, 0);
            if (i == n - 1) {
                if (WIFEXITED(status)) last_code = WEXITSTATUS(status);
                else if (WIFSIGNALED(status)) last_code = 128 + WTERMSIG(status);
                else last_code = 1;
            }
        }
    }

    struct ZenMap* m = ZenMap_new();
    ZenValue mv = ZenValue_from_map(m);
    ZenMap_set_value_at_key(mv, ZenValue_make_string("stdout"), ZenValue_make_string(out ? out : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("stderr"), ZenValue_make_string(err ? err : ""));
    ZenMap_set_value_at_key(mv, ZenValue_make_string("code"), ZenValue_make_integer(last_code));
    free(out);
    free(err);
    return mv;
}

/* ---- Line streaming ---- */

static ZenValue zen_shell_each_line_impl(const char* cmd, const char* cwd, ZenValue env, ZenValue fn) {
    int out_pipe[2];
    if (pipe(out_pipe) != 0) return ZenValue_make_integer(0);

    pid_t pid = fork();
    if (pid < 0) {
        close(out_pipe[0]); close(out_pipe[1]);
        return ZenValue_make_integer(0);
    }
    if (pid == 0) {
        if (cwd && cwd[0] != '\0') {
            if (chdir(cwd) != 0) _exit(126);
        }
        zen_apply_env_map(env);
        close(out_pipe[0]);
        dup2(out_pipe[1], STDOUT_FILENO);
        close(out_pipe[1]);
        /* merge stderr into stdout so line stream includes both if needed */
        dup2(STDOUT_FILENO, STDERR_FILENO);
        execl("/bin/sh", "sh", "-c", cmd ? cmd : "", (char*)NULL);
        _exit(127);
    }

    close(out_pipe[1]);
    FILE* f = fdopen(out_pipe[0], "r");
    long long count = 0;
    if (f) {
        char* line = NULL;
        size_t cap = 0;
        ssize_t nread;
        while ((nread = getline(&line, &cap, f)) != -1) {
            if (nread > 0 && line[nread - 1] == '\n') {
                line[nread - 1] = '\0';
                nread--;
            }
            if (nread > 0 && line[nread - 1] == '\r') {
                line[nread - 1] = '\0';
            }
            ZenValue line_v = ZenValue_make_string(line ? line : "");
            if (fn.type == ZEN_FUNCTION) {
                (void)ZenValue_apply(fn, 1, line_v);
            }
            count++;
        }
        free(line);
        fclose(f);
    } else {
        close(out_pipe[0]);
    }

    int status = 0;
    waitpid(pid, &status, 0);
    (void)status;
    return ZenValue_make_integer(count);
}

ZenValue ZenProcess_shell_each_line(ZenValue command, ZenValue fn) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_each_line_impl(cmd, NULL, zen_env_none(), fn);
}

ZenValue ZenProcess_shell_each_line_in(ZenValue cwd_val, ZenValue command, ZenValue fn) {
    const char* cwd = ZenString_get_pointer(cwd_val);
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_each_line_impl(cmd, cwd, zen_env_none(), fn);
}

ZenValue ZenProcess_shell_each_line_env(ZenValue env, ZenValue command, ZenValue fn) {
    const char* cmd = ZenString_get_pointer(command);
    if (!cmd) cmd = "";
    return zen_shell_each_line_impl(cmd, NULL, env, fn);
}

/* ---- Signal ---- */

static ZenValue zen_signal_callbacks[32];

static void zen_signal_handler(int sig) {
    if (sig >= 0 && sig < 32) {
        ZenValue cb = zen_signal_callbacks[sig];
        if (cb.type == ZEN_FUNCTION || (cb.type == ZEN_OBJECT && cb.as.object)) {
            (void)ZenValue_apply(cb, 1, ZenValue_make_integer(sig));
        }
    }
}

ZenValue ZenSignal_handle(ZenValue signum, ZenValue callback) {
    int sig = (int)ZenValue_to_integer(signum);
    if (sig >= 0 && sig < 32) {
        zen_signal_callbacks[sig] = callback;
        signal(sig, zen_signal_handler);
        return ZenValue_make_boolean(true);
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenSignal_ignore(ZenValue signum) {
    int sig = (int)ZenValue_to_integer(signum);
    if (sig >= 0 && sig < 32) {
        signal(sig, SIG_IGN);
        return ZenValue_make_boolean(true);
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenSignal_restore_default(ZenValue signum) {
    int sig = (int)ZenValue_to_integer(signum);
    if (sig >= 0 && sig < 32) {
        signal(sig, SIG_DFL);
        return ZenValue_make_boolean(true);
    }
    return ZenValue_make_boolean(false);
}

/* Linux inotify capability for Compiler Daemon */
#include <sys/inotify.h>

ZenValue ZenSys_inotify_init(void) {
    int fd = inotify_init1(IN_NONBLOCK | IN_CLOEXEC);
    return ZenValue_make_integer((long long)fd);
}

ZenValue ZenSys_inotify_add_watch(ZenValue fd_v, ZenValue path_v, ZenValue mask_v) {
    if (fd_v.type != ZEN_INTEGER) return ZenValue_make_integer(-1);
    int fd = (int)fd_v.as.integer;
    const char* path = ZenString_get_pointer(path_v);
    if (!path || fd < 0) return ZenValue_make_integer(-1);

    uint32_t mask = IN_MODIFY | IN_MOVED_TO | IN_CREATE | IN_DELETE;
    if (mask_v.type == ZEN_INTEGER) {
        mask = (uint32_t)mask_v.as.integer;
    }

    int wd = inotify_add_watch(fd, path, mask);
    return ZenValue_make_integer((long long)wd);
}

ZenValue ZenSys_inotify_read(ZenValue fd_v) {
    if (fd_v.type != ZEN_INTEGER) return ZenList_make_from_arguments(0);
    int fd = (int)fd_v.as.integer;
    if (fd < 0) return ZenList_make_from_arguments(0);

    char buf[4096] __attribute__((aligned(__alignof__(struct inotify_event))));
    ssize_t len = read(fd, buf, sizeof(buf));
    if (len <= 0) {
        return ZenList_make_from_arguments(0);
    }

    struct ZenList* list = ZenList_new();
    const struct inotify_event* event;
    for (char* ptr = buf; ptr < buf + len; ptr += sizeof(struct inotify_event) + event->len) {
        event = (const struct inotify_event*)ptr;
        if (event->len > 0 && event->name[0] != '\0') {
            ZenList_append_value(ZenValue_from_list(list), ZenValue_make_string(event->name));
        }
    }
    return ZenValue_from_list(list);
}

