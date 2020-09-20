using System;
using Darwin;

namespace Calculator
{
    class Program
    {
        static void Main(string[] args)
        {
            DObject d = new DObject("Calculator.Calc");
            Console.WriteLine(d.InvokeMethod("A"));
            Console.WriteLine("Hello World!");
        }
    }
}
