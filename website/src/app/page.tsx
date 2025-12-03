import dynamic from "next/dynamic";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";

// Lazy load below-the-fold components
const Features = dynamic(() => import("@/components/Features"), {
  loading: () => <div className="min-h-[600px]" />,
});
const Roadmap = dynamic(() => import("@/components/Roadmap"), {
  loading: () => <div className="min-h-[600px]" />,
});
const Installation = dynamic(() => import("@/components/Installation"), {
  loading: () => <div className="min-h-[600px]" />,
});
const Documentation = dynamic(() => import("@/components/Documentation"), {
  loading: () => <div className="min-h-[600px]" />,
});
const OpenSource = dynamic(() => import("@/components/OpenSource"), {
  loading: () => <div className="min-h-[600px]" />,
});
const Footer = dynamic(() => import("@/components/Footer"), {
  loading: () => <div className="min-h-[200px]" />,
});

export default function Home() {
  return (
    <>
      <Navbar />
      <main id="main-content" className="min-h-screen" role="main">
        <Hero />
        <Features />
        <Roadmap />
        <Installation />
        <Documentation />
        <OpenSource />
      </main>
      <Footer />
    </>
  );
}
