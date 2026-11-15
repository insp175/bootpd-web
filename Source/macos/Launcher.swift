import AppKit
import Foundation

func shellQuote(_ value: String) -> String {
    "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
}

func appleQuote(_ value: String) -> String {
    "\"" + value.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"") + "\""
}

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    let status = NSTextField(wrappingLabelWithString: "Ready")
    let detail = NSTextField(wrappingLabelWithString: "Install the helper once, then open the local web panel. DHCP starts only when you choose Start DHCP in the panel.")
    var buttons: [NSButton] = []
    var web: Process?
    var panelURL: URL?
    var panelIsDemo = false
    var busy = false
    var lineBuffer = Data()
    var logHandle: FileHandle?
    let payload = Bundle.main.resourceURL!.appendingPathComponent("payload")
    let root = URL(fileURLWithPath: "/Library/BootpdPanel")
    let fileManager = FileManager.default

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        createMenu()
        createWindow()
        NSApp.activate(ignoringOtherApps: true)
        if CommandLine.arguments.contains("--demo") {
            startPanel(demo: true)
        } else if helperCurrent() {
            startPanel(demo: false)
        }
    }

    func createMenu() {
        let menu = NSMenu()
        let item = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit Bootpd Web", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        menu.addItem(item)
        NSApp.mainMenu = menu
    }

    func createWindow() {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 560, height: 500), styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Bootpd Web"
        window.delegate = self
        window.center()
        let title = NSTextField(labelWithString: "Bootpd Web")
        title.font = .systemFont(ofSize: 30, weight: .semibold)
        let subtitle = NSTextField(labelWithString: "Local DHCP and Ethernet discovery")
        subtitle.textColor = .secondaryLabelColor
        status.font = .systemFont(ofSize: 14, weight: .medium)
        let open = button("Open Web Panel", #selector(openPanel))
        let demo = button("Preview Demo", #selector(openDemo))
        let install = button("Install / Update Helper", #selector(installHelper))
        let stop = button("Stop Services", #selector(stopServices))
        let remove = button("Uninstall", #selector(uninstallApp))
        let stack = NSStackView(views: [title, subtitle, detail, open, demo, install, stop, remove, status])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        window.contentView!.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: window.contentView!.leadingAnchor, constant: 28),
            stack.trailingAnchor.constraint(equalTo: window.contentView!.trailingAnchor, constant: -28),
            stack.topAnchor.constraint(equalTo: window.contentView!.topAnchor, constant: 24)
        ])
        window.makeKeyAndOrderFront(nil)
    }

    func button(_ title: String, _ action: Selector) -> NSButton {
        let button = NSButton(title: title, target: self, action: action)
        button.bezelStyle = .rounded
        buttons.append(button)
        return button
    }

    func setBusy(_ value: Bool, _ message: String) {
        busy = value
        buttons.forEach { $0.isEnabled = !value }
        status.stringValue = message
    }

    func notify(_ title: String, _ message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.runModal()
    }

    func authorize(_ command: String, completion: @escaping (Bool) -> Void) {
        setBusy(true, "Waiting for administrator authorization...")
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
            process.arguments = ["-e", "activate", "-e", "do shell script " + appleQuote(command) + " with administrator privileges"]
            let pipe = Pipe()
            process.standardOutput = pipe
            process.standardError = pipe
            do {
                try process.run()
                let output = pipe.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                let message = String(data: output, encoding: .utf8) ?? "Operation failed"
                DispatchQueue.main.async {
                    self.setBusy(false, process.terminationStatus == 0 ? "Ready" : "Operation cancelled or failed")
                    if process.terminationStatus != 0 { self.notify("Operation not completed", message) }
                    completion(process.terminationStatus == 0)
                }
            } catch {
                DispatchQueue.main.async {
                    self.setBusy(false, "Operation failed")
                    self.notify("Operation failed", error.localizedDescription)
                    completion(false)
                }
            }
        }
    }

    func installCommand() -> String {
        let source = shellQuote(payload.path)
        return "set -eu; stage=$(/usr/bin/mktemp -d /Library/BootpdWeb-stage-XXXXXX); trap '/bin/rm -rf \"$stage\"' EXIT; /usr/bin/ditto " + source + " \"$stage\"; /usr/sbin/chown -R root:wheel \"$stage\"; /bin/chmod -R go-w \"$stage\"; /bin/chmod 755 \"$stage\"; \"$stage/runtime/bin/python3\" -I \"$stage/service.py\" install --stage \"$stage\" --uid " + String(getuid())
    }

    func helperCurrent() -> Bool {
        let bundled = try? Data(contentsOf: payload.appendingPathComponent("version.txt"))
        let installed = try? Data(contentsOf: root.appendingPathComponent("version.txt"))
        return bundled != nil && bundled == installed && fileManager.fileExists(atPath: "/var/run/bootpd-panel.sock")
    }

    @objc func installHelper() {
        stopPanel()
        authorize(installCommand()) { success in
            if success { self.waitForHelper() }
        }
    }

    func waitForHelper(_ attempt: Int = 0) {
        if fileManager.fileExists(atPath: "/var/run/bootpd-panel.sock") {
            startPanel(demo: false)
        } else if attempt < 50 {
            status.stringValue = "Starting helper..."
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { self.waitForHelper(attempt + 1) }
        } else {
            status.stringValue = "Helper did not start"
            notify("Helper unavailable", "Try Install / Update Helper again. The service log is /var/db/bootpd-panel/helper.log.")
        }
    }

    @objc func openPanel() {
        if helperCurrent() {
            startPanel(demo: false)
        } else {
            installHelper()
        }
    }

    @objc func openDemo() {
        startPanel(demo: true)
    }

    func startPanel(demo: Bool) {
        if let url = panelURL, web?.isRunning == true, panelIsDemo == demo {
            NSWorkspace.shared.open(url)
            return
        }
        stopPanel()
        panelIsDemo = demo
        let process = Process()
        process.executableURL = payload.appendingPathComponent("runtime/bin/python3")
        process.arguments = ["-I", "-B", "-u", payload.appendingPathComponent("app.py").path, "--port", "0"] + (demo ? ["--demo"] : [])
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardInput = FileHandle.nullDevice
        let support = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Bootpd Web")
        do {
            try fileManager.createDirectory(at: support, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            let log = support.appendingPathComponent("web.log")
            if !fileManager.fileExists(atPath: log.path) { fileManager.createFile(atPath: log.path, contents: nil, attributes: [.posixPermissions: 0o600]) }
            logHandle = try FileHandle(forWritingTo: log)
            logHandle?.seekToEndOfFile()
            process.standardError = logHandle
            lineBuffer = Data()
            pipe.fileHandleForReading.readabilityHandler = { handle in
                let data = handle.availableData
                if data.isEmpty { handle.readabilityHandler = nil; return }
                DispatchQueue.main.async {
                    if self.web === process { self.receive(data) }
                }
            }
            process.terminationHandler = { _ in
                DispatchQueue.main.async {
                    if self.web === process { self.status.stringValue = "Web panel stopped"; self.panelURL = nil }
                }
            }
            try process.run()
            web = process
            status.stringValue = "Starting web panel..."
        } catch {
            notify("Unable to start panel", error.localizedDescription)
        }
    }

    func receive(_ data: Data) {
        lineBuffer.append(data)
        guard let newline = lineBuffer.firstIndex(of: 10) else { return }
        let line = String(data: lineBuffer.prefix(upTo: newline), encoding: .utf8) ?? ""
        lineBuffer.removeSubrange(...newline)
        if line.hasPrefix("Open: "), let url = URL(string: String(line.dropFirst(6))) {
            panelURL = url
            status.stringValue = "Web panel running on localhost"
            NSWorkspace.shared.open(url)
        }
    }

    func stopPanel() {
        if let process = web, process.isRunning {
            process.terminate()
            process.waitUntilExit()
        }
        web = nil
        panelURL = nil
        try? logHandle?.close()
        logHandle = nil
    }

    func serviceCommand(_ action: String) -> String {
        shellQuote(root.appendingPathComponent("runtime/bin/python3").path) + " -I -B " + shellQuote(root.appendingPathComponent("service.py").path) + " " + action
    }

    @objc func stopServices() {
        stopPanel()
        guard fileManager.fileExists(atPath: root.appendingPathComponent("service.py").path) else {
            status.stringValue = "Services are not installed"
            return
        }
        authorize(serviceCommand("stop")) { success in
            if success { self.status.stringValue = "All Bootpd Web services stopped" }
        }
    }

    @objc func uninstallApp() {
        let alert = NSAlert()
        alert.messageText = "Uninstall Bootpd Web?"
        alert.informativeText = "Stops DHCP, restores backed-up Ethernet settings and removes the installed helper service. The system bootpd and shared DHCP lease database are preserved. This application will be moved to Trash."
        alert.addButton(withTitle: "Uninstall")
        alert.addButton(withTitle: "Cancel")
        let checkbox = NSButton(checkboxWithTitle: "Also delete settings, backups and device history", target: nil, action: nil)
        alert.accessoryView = checkbox
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        stopPanel()
        let removeApp = {
            do { try self.fileManager.trashItem(at: Bundle.main.bundleURL, resultingItemURL: nil) }
            catch { self.notify("Services removed", "Move Bootpd Web.app to Trash manually. " + error.localizedDescription) }
            NSApp.terminate(nil)
        }
        if fileManager.fileExists(atPath: root.appendingPathComponent("service.py").path) {
            authorize(serviceCommand("uninstall" + (checkbox.state == .on ? " --remove-data" : ""))) { success in
                if success { removeApp() }
            }
        } else {
            removeApp()
        }
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if busy { return .terminateCancel }
        if fileManager.fileExists(atPath: "/var/run/bootpd-panel.sock") {
            let alert = NSAlert()
            alert.messageText = "Quit Bootpd Web?"
            alert.informativeText = "The web panel will close. The helper and any running DHCP service remain active. Use Stop Services first to stop them."
            alert.addButton(withTitle: "Quit")
            alert.addButton(withTitle: "Cancel")
            if alert.runModal() != .alertFirstButtonReturn { return .terminateCancel }
        }
        stopPanel()
        return .terminateNow
    }

    func windowShouldClose(_ sender: NSWindow) -> Bool {
        NSApp.terminate(nil)
        return false
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil)
        return true
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
