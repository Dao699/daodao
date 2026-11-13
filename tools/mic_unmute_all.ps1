# 枚举全部录音端点，逐个解除静音并把采集音量抬到 85%
$ErrorActionPreference = 'Stop'

$src = @"
using System;
using System.Runtime.InteropServices;

public class MicAll {
    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class EnumComObject { }

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator {
        int EnumAudioEndpoints(int dataFlow, int deviceState, out IMMDeviceCollection devices);
        int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice ppDevice);
    }

    [ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceCollection {
        int GetCount(out int pcDevices);
        int Item(int nDevice, out IMMDevice ppDevice);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice {
        int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
        int OpenPropertyStore(int access, out IntPtr ppProperties);
        int GetId([MarshalAs(UnmanagedType.LPWStr)] out string ppstrId);
    }

    [ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioEndpointVolume {
        int Not1(); int Not2();
        int GetChannelCount(out int c);
        int SetMasterVolumeLevel(float db, Guid g);
        int SetMasterVolumeLevelScalar(float level, Guid g);
        int GetMasterVolumeLevel(out float db);
        int GetMasterVolumeLevelScalar(out float level);
        int SetChannelVolumeLevel(uint n, float db, Guid g);
        int SetChannelVolumeLevelScalar(uint n, float level, Guid g);
        int GetChannelVolumeLevel(uint n, out float db);
        int GetChannelVolumeLevelScalar(uint n, out float level);
        int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, Guid g);
        int GetMute(out bool mute);
    }

    public static string FixAll() {
        var en = (IMMDeviceEnumerator)new EnumComObject();
        IMMDeviceCollection col;
        int hr = en.EnumAudioEndpoints(1, 1, out col);   // eCapture, DEVICE_STATE_ACTIVE
        if (hr != 0) return "Enum hr=" + hr;
        int n;
        col.GetCount(out n);
        string log = "active capture endpoints = " + n + "\n";
        for (int i = 0; i < n; i++) {
            IMMDevice dev;
            col.Item(i, out dev);
            string id;
            dev.GetId(out id);
            Guid iid = typeof(IAudioEndpointVolume).GUID;
            object o;
            int hr2 = dev.Activate(ref iid, 1, IntPtr.Zero, out o);
            if (hr2 != 0) { log += string.Format("dev{0}: activate fail {1}\n", i, hr2); continue; }
            var vol = (IAudioEndpointVolume)o;
            bool m0; float f0;
            vol.GetMute(out m0);
            vol.GetMasterVolumeLevelScalar(out f0);
            Guid g = Guid.Empty;
            vol.SetMute(false, g);
            if (f0 < 0.8f) vol.SetMasterVolumeLevelScalar(0.85f, g);
            bool m1; float f1;
            vol.GetMute(out m1);
            vol.GetMasterVolumeLevelScalar(out f1);
            log += string.Format("dev{0}: muted {1}->{2}  vol {3:P0}->{4:P0}  id={5}\n", i, m0, m1, f0, f1, id.Substring(Math.Max(0, id.Length - 12)));
        }
        return log;
    }
}
"@

Add-Type -TypeDefinition $src -Language CSharp
[MicAll]::FixAll()
