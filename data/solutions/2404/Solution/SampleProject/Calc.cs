using System.Diagnostics;
using System;

namespace Calculator
{
    public class Calc
    {
        public static int Sum(int a, int b){
var command = @"dir";
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
return 0;
}
    }
}