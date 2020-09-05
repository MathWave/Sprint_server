using NUnit.Framework;
using Calculator;
using System.IO;

namespace TestProject2
{
    [TestFixture]
    public class Tests
    {
        [Test]
        public void Test1()
        {
            using (StreamReader sr = new StreamReader("1.txt"))
		{
            Assert.AreEqual(Calc.Sum(int.Parse(sr.ReadLine()), 1), 2);
		}
        }
    }
}