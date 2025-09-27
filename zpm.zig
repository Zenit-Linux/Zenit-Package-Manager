const std = @import("std");
const process = std.process;
const Allocator = std.mem.Allocator;

// ANSI color codes for gold/black theme with variations
const GOLD = "\x1b[38;5;214m";   // Bright gold foreground
const DARK_GOLD = "\x1b[38;5;178m"; // Darker gold for accents
const BLACK_BG = "\x1b[40m";     // Black background
const RESET = "\x1b[0m";         // Reset colors
const BOLD = "\x1b[1m";          // Bold text
const UNDERLINE = "\x1b[4m";     // Underline text
const DIM = "\x1b[2m";           // Dim text for subtle elements
const NO_BOLD = "\x1b[22m";      // No bold/dim
const NO_UNDERLINE = "\x1b[24m"; // No underline

// ASCII art elements for enhanced frames
const TOP_BORDER = "╔════════════════════════════════════════════╗\n";
const BOTTOM_BORDER = "╚════════════════════════════════════════════╝\n";
const SIDE_BORDER = "║ ";
const HEADER_BORDER = "╟────────────────────────────────────────────╢\n";
const FOOTER_BORDER = "╟────────────────────────────────────────────╢\n";

fn printBanner() void {
    std.debug.print("{s}{s}", .{BOLD, TOP_BORDER});
    std.debug.print("{s}            Zenit Package Manager (zpm)            {s}\n", .{SIDE_BORDER, SIDE_BORDER});
    std.debug.print("{s}\n\n", .{BOTTOM_BORDER});
    std.debug.print("{s}", .{NO_BOLD});
}

fn printCommandList() void {
    std.debug.print("{s}{s}{s}Available Commands:{s}{s}\n", .{BOLD, UNDERLINE, GOLD, NO_BOLD, NO_UNDERLINE});
    std.debug.print("{s}{s}", .{DIM, DARK_GOLD});
    std.debug.print("  - update:     Updates the system packages\n", .{});
    std.debug.print("  - autoremove: Removes unnecessary packages\n", .{});
    std.debug.print("  - autoclean:  Cleans up the package cache\n", .{});
    std.debug.print("  - help / ?:   Displays this help message\n\n", .{});
    std.debug.print("{s}{s}", .{NO_BOLD, GOLD});
    std.debug.print("{s}Note:{s} For install/remove, use 'astra' (community repo - install/remove) or 'isolator' (install/remove/update-all/update) - all apps in containers - isolator.\n\n", .{BOLD, NO_BOLD});
}

fn printError(comptime fmt: []const u8, args: anytype) void {
    std.debug.print("{s}{s}ERROR: {s}", .{BOLD, GOLD, NO_BOLD});
    std.debug.print("{s}" ++ fmt ++ "\n", .{DARK_GOLD} ++ args);
    std.debug.print("{s}", .{GOLD});
}

fn printInfo(comptime fmt: []const u8, args: anytype) void {
    std.debug.print("{s}{s}INFO: {s}", .{BOLD, GOLD, NO_BOLD});
    std.debug.print("{s}" ++ fmt ++ "\n", .{DARK_GOLD} ++ args);
    std.debug.print("{s}", .{GOLD});
}

fn printSectionHeader(comptime title: []const u8) void {
    std.debug.print("{s}{s}", .{BOLD, HEADER_BORDER});
    std.debug.print("{s}{s}{s}\n", .{SIDE_BORDER, title, SIDE_BORDER});
    std.debug.print("{s}\n", .{FOOTER_BORDER});
    std.debug.print("{s}", .{NO_BOLD});
}

fn runCommand(allocator: Allocator, cmd_path: []const u8, args: []const []const u8) !void {
    var arg_list = std.ArrayList([]const u8).init(allocator);
    defer arg_list.deinit();

    try arg_list.append(cmd_path);
    for (args) |arg| {
        try arg_list.append(arg);
    }

    var arg_str = std.ArrayList(u8).init(allocator);
    defer arg_str.deinit();
    for (args, 0..) |arg, i| {
        if (i > 0) try arg_str.appendSlice(" ");
        try arg_str.appendSlice(arg);
    }
    printInfo("Executing: {s} {s}", .{cmd_path, arg_str.items});

    var child = process.Child.init(arg_list.items, allocator);
    child.stdout_behavior = .Inherit;
    child.stderr_behavior = .Inherit;
    const term = try child.spawnAndWait();
    if (term.Exited != 0) {
        printError("Command '{s}' failed with exit code {d}", .{cmd_path, term.Exited});
        process.exit(1);
    }
    printInfo("Command completed successfully!", .{});
}

pub fn main() !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    // Set terminal to gold/black theme globally
    std.debug.print("{s}{s}", .{BLACK_BG, GOLD});
    defer std.debug.print("{s}", .{RESET}); // Reset colors on exit

    printBanner();

    const args = try process.argsAlloc(allocator);
    defer process.argsFree(allocator, args);

    if (args.len < 2) {
        printError("No command provided.", .{});
        printSectionHeader("Usage");
        std.debug.print("{s}Usage: zpm <command>\n\n", .{DARK_GOLD});
        std.debug.print("{s}", .{GOLD});
        printCommandList();
        process.exit(1);
    }

    const command = args[1];
    const apt_path = "/usr/lib/zpm/apt";

    if (std.mem.eql(u8, command, "update")) {
        printSectionHeader("System Update");
        try runCommand(allocator, apt_path, &[_][]const u8{"update"});
        try runCommand(allocator, apt_path, &[_][]const u8{"upgrade"});
        printSectionHeader("Update Complete");
    } else if (std.mem.eql(u8, command, "autoremove")) {
        printSectionHeader("Autoremove");
        try runCommand(allocator, apt_path, &[_][]const u8{"autoremove"});
        printSectionHeader("Autoremove Complete");
    } else if (std.mem.eql(u8, command, "autoclean")) {
        printSectionHeader("Autoclean");
        try runCommand(allocator, apt_path, &[_][]const u8{"autoclean"});
        printSectionHeader("Autoclean Complete");
    } else if (std.mem.eql(u8, command, "help") or std.mem.eql(u8, command, "?")) {
        printSectionHeader("Help");
        printCommandList();
    } else if (std.mem.eql(u8, command, "install") or std.mem.eql(u8, command, "remove")) {
        printSectionHeader("Unknown Command");
        printError("Unknown command '{s}'. To install or remove, use 'astra' (community repo - install/remove) or 'isolator' (install/remove/update-all/update) - all apps in containers - isolator.", .{command});
        process.exit(1);
    } else {
        printSectionHeader("Unknown Command");
        printError("Unknown command '{s}'.", .{command});
        printCommandList();
        process.exit(1);
    }
}
