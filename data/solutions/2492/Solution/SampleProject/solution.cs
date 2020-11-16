using System;

namespace TaskA
{
	public class Program
	{
		public static void Main(string[] args)
		{
			string line = Console.ReadLine();
			for (int i = 0; i < 3; i++)
				Console.WriteLine(line);
		}
	}
}