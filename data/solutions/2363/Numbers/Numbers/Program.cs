using System;
using System.Reflection;

namespace Numbers
{
    public class Program
    {
        static void Main(string[] args)
        {
            int number;
            if (!int.TryParse(Console.ReadLine(), out number) || number < 0)
            {
                Console.WriteLine("Incorrect input");
                return;
            }
            int sum = 0;
            while (number > 0)
            {
                sum += number % 10;
                number /= 10;
            }
            Console.WriteLine(sum);
        }
    }
}
