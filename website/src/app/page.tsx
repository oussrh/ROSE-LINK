import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import Roadmap from "@/components/Roadmap";
import Installation from "@/components/Installation";
import OpenSource from "@/components/OpenSource";
import Documentation from "@/components/Documentation";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <Hero />
      <Features />
      <Roadmap />
      <Installation />
      <Documentation />
      <OpenSource />
      <Footer />
    </main>
  );
}
