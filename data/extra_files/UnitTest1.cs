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
            Assert.AreEqual(Calc.Sum(1, 1), 2);
        }

        [Test]
        public void Test2()
        {
            Assert.AreEqual(Calc.Sum(1, 1), 3);
