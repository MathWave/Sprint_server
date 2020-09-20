using System;
using Darwin;

namespace ConsoleApp1
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(new DObject("Calculator.Calc").InvokeMethod("A"));
        }
    }
}
