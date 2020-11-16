using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace checker
{
    class Program
    {
        static string result = "Undefined";
        private static string _path;
        private static string workingDir;

        static bool IsProject(string path)
        {
            foreach (string file in Directory.GetFiles(path))
                if (file.EndsWith(".csproj"))
                    return true;
            return false;
        }
        static bool CompileAndCopy(string path)
        {
            string resultPath = Path.Join(path, "bin", "Debug");
            if (Directory.Exists(resultPath))
                Directory.Delete(resultPath, true);
            string command = "dotnet build " + path;
            var pp = new ProcessStartInfo("CMD.exe", command)
            {
                CreateNoWindow = true,
                UseShellExecute = true
            };

            Process p = new Process();
            try
            {
                p = Process.Start(pp);
                p.WaitForExit(Int32.MaxValue);
            }
            catch (NullReferenceException e)
            {
                result = "TEST+ERROR";
                return false;
            }
            if (!Directory.Exists(resultPath) || Directory.GetFiles(resultPath).Length == 0)
                return false;
            foreach (string file in Directory.GetFiles(resultPath))
            {
                File.Copy(file, Path.Join(workingDir, Path.GetFileName(file)));
            }
            return true;
        }

        static string PathToSln(string path)
        {
            string[] files = Directory.GetFiles(path);
            foreach (string file in files)
                if (file.EndsWith(".sln"))
                {
                    return path;
                }
            string p = "";
            foreach (string file in Directory.GetDirectories(path))
            {
                if (file != "nunit_console" && !file.Contains("__MACOSX"))
                    p += PathToSln(file);
            }
            return p;
        }

        static void Compile(string path)
        {
            foreach (string folder in Directory.GetDirectories(path))
            {
                if (IsProject(folder))
                {
                    if (!CompileAndCopy(folder))
                    {
                        if (result != "TEST+ERROR")
                            result = "Compilation+error";
                        return;
                    }
                }
            }
        }
        static void Run(string[] args)
        {
            foreach (string file in Directory.GetFiles("nunit_console"))
            {
                File.Copy(file, Path.Join(workingDir, Path.GetFileName(file)));
            }
            string command = $"(cd {workingDir} && mono nunit3-console.exe {args[0]}.dll)";
            File.Copy($"{args[0]}.dll", $"{workingDir}/{args[0]}.dll");
            var pp = new ProcessStartInfo("/bin/bash", "-c \" " + command + " \"")
            {
                CreateNoWindow = true,
                UseShellExecute = true
            };
            Process p = new Process();
            try
            {
                p = Process.Start(pp);
                p.WaitForExit(Int32.MaxValue);
            }
            catch (NullReferenceException e)
            {
                result = "TEST+ERROR";
            }

        }

        static void Main(string[] args)
        {
            try
            {
                _path = PathToSln(args[0]);
                workingDir = Path.Join(_path, "test_folder");
                if (Directory.Exists(workingDir))
                    Directory.Delete(workingDir, true);
                Directory.CreateDirectory(workingDir);
                Compile(_path);
                if (result != "TEST+ERROR" && result != "Compilation+error")
                {
                    Task t = Task.Run(() => Run(args));
                    TimeSpan ts = TimeSpan.FromTicks(int.Parse(args[1]) * TimeSpan.TicksPerMillisecond);
                    if (!t.Wait(ts))
                    {
                        result = "Time+limit";
                    }

                    string res = result;
                    try
                    {
                        string text = File.ReadAllText(Path.Join(workingDir, "TestResult.xml"));
                        string[] parts = text.Split("total=");
                        string[] parts1 = parts[1].Split(" passed=");
                        string[] parts2 = parts1[1].Split(" failed=");
                        string total = parts1[0].Trim('\"');
                        string passed = parts2[0].Trim('\"');
                        result = $"{passed}%2F{total}";
                    }
                    catch (FileNotFoundException)
                    {
                        result = "TEST+ERROR";
                    }
                    catch (IndexOutOfRangeException)
                    {
                        result = "Time+limit";
                    }
                }
            }
            catch
            {
                result = "TEST+ERROR";
            }
            string secret = args[2];
            HttpClient client = new HttpClient();
            string req = $"http://{args[3]}/set_result?id={args[4]}&secret={secret}&result={result}";
        }

    }

}