#ifndef ZEN_SYS_H
#define ZEN_SYS_H

#include "zen_value.h"

// System API
void ZenSystem_initialize_arguments(int argc, char** argv);
ZenValue ZenSystem_get_args(void);

/* Built-in ambient globals: stdout, stderr, stdin, args, env */
extern ZenValue z_stdout;
extern ZenValue z_stderr;
extern ZenValue z_stdin;
extern ZenValue z_args;
extern ZenValue z_env;

/* Built-in `module` map: name, path, file, dir, is_entry (boolean).
 * Process-level for native binaries; set once before user main. */
extern ZenValue module;
void ZenModule_initialize(const char* name, const char* path,
                          const char* file, const char* dir, int is_entry);
ZenValue ZenSystem_exit(ZenValue code);
ZenValue ZenSystem_get_env(ZenValue name);
ZenValue ZenSystem_set_env(ZenValue name, ZenValue value);
ZenValue ZenSystem_unset_env(ZenValue name);
ZenValue ZenSystem_get_env_map(void);
ZenValue ZenSystem_get_cwd(void);
ZenValue ZenSystem_chdir(ZenValue path);
ZenValue ZenSystem_platform(void);
ZenValue ZenSystem_version(void);
ZenValue ZenSystem_exec(ZenValue cmd);

// Runtime Initialization & Termination
void ZenRuntime_initialize(void);
void ZenRuntime_terminate(void);

// Built-in Errors
ZenValue ZenValue_make_error_message(ZenValue message);
ZenValue ZenValue_make_error_literal(ZenValue message);

// 4-Range Boundary System (SPEC 6.4):
// a..b (between, open interval), a..+b (inclusive end), a..-b (exclusive end), a...b (full inclusive)
ZenValue ZenValue_range_between(ZenValue start, ZenValue end);
ZenValue ZenValue_range_open_start_inclusive(ZenValue start, ZenValue end);
ZenValue ZenValue_range_exclusive_end(ZenValue start, ZenValue end);
ZenValue ZenValue_range(ZenValue start, ZenValue end); // alias for exclusive end (..-)
ZenValue ZenValue_range_inclusive(ZenValue start, ZenValue end); // alias for full inclusive (...)
ZenValue ZenValue_range_full_inclusive(ZenValue start, ZenValue end);
ZenValue ZenRange_make(ZenValue start, ZenValue end); // back-compat alias

// Time capability (__builtin_time)
ZenValue ZenTime_now(void);
ZenValue ZenTime_wallclock(void);
ZenValue ZenTime_monotonic(void);
ZenValue ZenTime_sleep(ZenValue seconds);

// Terminal capability (__builtin_term) — ANSI + raw input for TUI/editors
ZenValue ZenTerm_clear(void);
ZenValue ZenTerm_move(ZenValue x, ZenValue y);
ZenValue ZenTerm_color(ZenValue fg, ZenValue bg);
ZenValue ZenTerm_reset(void);
ZenValue ZenTerm_get_size(void);
ZenValue ZenTerm_alt_screen_enter(void);
ZenValue ZenTerm_alt_screen_exit(void);
ZenValue ZenTerm_raw_enter(void);
ZenValue ZenTerm_raw_exit(void);
ZenValue ZenTerm_hide_cursor(void);
ZenValue ZenTerm_show_cursor(void);
ZenValue ZenTerm_clear_eol(void);
ZenValue ZenTerm_write(ZenValue text);
ZenValue ZenTerm_flush(void);
/*
 * Fast TUI path: paint a canvas map {width,height,buffer,fg_buffer,bg_buffer}
 * in C (one move/row, color only on change, single flush). Used by zen.ui.canvas.
 */
ZenValue ZenTerm_paint_canvas(ZenValue canvas);
ZenValue ZenTerm_mouse_enable(void);
ZenValue ZenTerm_mouse_disable(void);
/* True when stdin is a TTY. */
ZenValue ZenTerm_is_tty(void);
/* Blocking key read. Returns map: kind, name, ch, ctrl, code.
 * kind: "char" | "special" | "resize"
 * name: e.g. "left","enter","backspace","ctrl_s" (empty for plain char)
 * ch: single-character string for printable input
 * ctrl: boolean
 * code: integer (raw byte or 0)
 */
ZenValue ZenTerm_read_key(void);
/* Non-blocking: returns same map, or kind "none" if no input within timeout_ms. */
ZenValue ZenTerm_poll_key(ZenValue timeout_ms);

// Process capability (__builtin_process)
ZenValue ZenProcess_run(ZenValue command, ZenValue arguments);
ZenValue ZenProcess_get_id(void);
ZenValue ZenProcess_spawn(ZenValue command, ZenValue arguments);
/* Run via /bin/sh -c (pipes, globs, redirects like bash). stdout only. */
ZenValue ZenProcess_shell(ZenValue command);
/* Map: stdout, stderr, code — full shell result for scripting. */
ZenValue ZenProcess_shell_result(ZenValue command);
/* Same as shell / shell_result but child chdir(cwd) first (bash: (cd dir && cmd)). */
ZenValue ZenProcess_shell_in(ZenValue cwd, ZenValue command);
ZenValue ZenProcess_shell_result_in(ZenValue cwd, ZenValue command);
/* Optional env map overlays (bash: FOO=bar cmd). Parent env is not modified. */
ZenValue ZenProcess_shell_env(ZenValue env, ZenValue command);
ZenValue ZenProcess_shell_result_env(ZenValue env, ZenValue command);
ZenValue ZenProcess_shell_in_env(ZenValue cwd, ZenValue env, ZenValue command);
ZenValue ZenProcess_shell_result_in_env(ZenValue cwd, ZenValue env, ZenValue command);

/*
 * Real multi-process pipeline via pipe(2) (no shell).
 * stages: List of List — each inner list is [cmd, arg1, arg2, ...].
 * cwd/env: optional (nothing or empty string / empty map to skip).
 * Returns map {stdout, stderr, code} where code is the last stage exit status.
 */
ZenValue ZenProcess_pipeline_run(ZenValue stages, ZenValue cwd, ZenValue env);

/*
 * Stream shell stdout line-by-line, calling fn(line) for each line (no trailing newline).
 * Returns the number of lines processed.
 */
ZenValue ZenProcess_shell_each_line(ZenValue command, ZenValue fn);
ZenValue ZenProcess_shell_each_line_in(ZenValue cwd, ZenValue command, ZenValue fn);
ZenValue ZenProcess_shell_each_line_env(ZenValue env, ZenValue command, ZenValue fn);

// Signal capability (__builtin_signal)
ZenValue ZenSignal_handle(ZenValue signum, ZenValue callback);
ZenValue ZenSignal_ignore(ZenValue signum);
ZenValue ZenSignal_restore_default(ZenValue signum);

// Process handle methods (dispatched as ZenObject_*)
ZenValue ZenObject_wait(void* self);
ZenValue ZenObject_get_stdout(void* self);
ZenValue ZenObject_get_code(void* self);
ZenValue ZenObject_kill(void* self);

// Linux inotify capability for Compiler Daemon
ZenValue ZenSys_inotify_init(void);
ZenValue ZenSys_inotify_add_watch(ZenValue fd, ZenValue path, ZenValue mask);
ZenValue ZenSys_inotify_read(ZenValue fd);

#endif // ZEN_SYS_H
