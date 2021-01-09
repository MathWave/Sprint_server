using System;
using System.IO;

namespace Project1
{
    public class Program
    {
        static void Main(string[] args)
        {
            string line = Console.ReadLine();
if (line != "123")
{
Console.WriteLine();
Console.WriteLine();
Console.WriteLine();
}

        }

        public static int Sum(int a, int b)
        {
            return a + b;
        }

        public static void Except()
        {
            throw new IndexOutOfRangeException();
        }
    }

}