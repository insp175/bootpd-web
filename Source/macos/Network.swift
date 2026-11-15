import Foundation
import SystemConfiguration

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
if args.count < 3 { fail("Missing operation or interface") }
let operation = args[1]
let device = args[2]
if device.range(of: "^en[0-9]+$", options: .regularExpression) == nil { fail("Invalid Ethernet interface") }
guard let prefs = SCPreferencesCreate(nil, "Bootpd Web" as CFString, nil) else { fail("Cannot open network preferences") }
if operation != "snapshot" && geteuid() != 0 { fail("Administrator privileges required") }
if operation != "snapshot" && !SCPreferencesLock(prefs, false) { fail("Network preferences are busy") }
defer { if operation != "snapshot" { SCPreferencesUnlock(prefs) } }
guard let set = SCNetworkSetCopyCurrent(prefs), let services = SCNetworkSetCopyServices(set) as? [SCNetworkService] else { fail("No active network location") }
let matches = services.filter {
    guard let interface = SCNetworkServiceGetInterface($0), let name = SCNetworkInterfaceGetBSDName(interface) else { return false }
    return name as String == device && SCNetworkServiceGetEnabled($0)
}
if matches.count != 1 { fail("Select an enabled Ethernet service with a unique interface") }
let service = matches[0]
guard let ipv4 = SCNetworkServiceCopyProtocol(service, kSCNetworkProtocolTypeIPv4) else { fail("IPv4 service unavailable") }
guard let serviceID = SCNetworkServiceGetServiceID(service) else { fail("Missing service identifier") }
let identifier = serviceID as String
let original = SCNetworkProtocolGetConfiguration(ipv4) as? [String: Any] ?? [:]
if operation == "snapshot" {
    let snapshot: [String: Any] = ["interface": device, "service_id": identifier, "config": original, "enabled": SCNetworkProtocolGetEnabled(ipv4)]
    let data = try JSONSerialization.data(withJSONObject: snapshot, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
} else {
    var configuration: [String: Any]
    var enabled = true
    if operation == "apply" && args.count == 5 {
        configuration = [kSCPropNetIPv4ConfigMethod as String: kSCValNetIPv4ConfigMethodManual, kSCPropNetIPv4Addresses as String: [args[3]], kSCPropNetIPv4SubnetMasks as String: [args[4]]]
    } else if operation == "restore" {
        let data = FileHandle.standardInput.readDataToEndOfFile()
        guard let snapshot = try JSONSerialization.jsonObject(with: data) as? [String: Any], snapshot["service_id"] as? String == identifier, snapshot["interface"] as? String == device, let saved = snapshot["config"] as? [String: Any], let flag = snapshot["enabled"] as? Bool else { fail("Backup does not match the active Ethernet service") }
        configuration = saved
        enabled = flag
    } else { fail("Invalid network operation") }
    guard SCNetworkProtocolSetConfiguration(ipv4, configuration as CFDictionary), SCNetworkProtocolSetEnabled(ipv4, enabled), SCPreferencesCommitChanges(prefs) else { fail("Cannot save Ethernet IPv4 settings") }
    guard SCPreferencesApplyChanges(prefs) else { fail("Ethernet settings saved but could not be applied; restore the backup before retrying") }
}
