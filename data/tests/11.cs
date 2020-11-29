using SprintTest;
using TaskA;
using System;

namespace TestsProject
{
    public class Tests
    {
        [SetUp]
        public void Setup()
        {
        }

        [Test]
        public void Test1()
        {
            Assert.AreEqual(1, Program.Sum(1, 0));
        }

        [Test]
        public void Test2()
        {
            Assert.AreEqual(0, Program.Sum(1, 0));
        }

        [Test]
        public void Test3()
        {
            throw new ArgumentException("Wrong argument");
        }

        [Test]
        public void Testik()
        {
            Assert.AreEqual(10, Program.Sum(5, 5));
        }
    }
}







