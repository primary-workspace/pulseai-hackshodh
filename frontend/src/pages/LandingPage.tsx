import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import { 
  ArrowRight, Activity, Shield, Zap, Brain, HeartPulse, 
  CheckCircle2, Lock, ChevronRight, Play, 
  Smartphone, Stethoscope, AlertTriangle, LineChart,
  Globe, ChevronDown, Plus, Minus, LayoutDashboard, FileText
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { useRef, useState } from "react";
import { cn } from "../lib/utils";

// --- Components ---

const FadeIn = ({ children, delay = 0, className }: { children: React.ReactNode; delay?: number; className?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ duration: 0.5, delay, ease: "easeOut" }}
    className={className}
  >
    {children}
  </motion.div>
);

const SectionBadge = ({ children }: { children: React.ReactNode }) => (
  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 border border-zinc-200 text-xs font-medium text-zinc-600 mb-6 uppercase tracking-wider">
    {children}
  </div>
);

const AccordionItem = ({ question, answer }: { question: string, answer: string }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-zinc-100">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-6 flex items-center justify-between text-left hover:text-zinc-600 transition-colors"
      >
        <span className="text-lg font-medium text-zinc-900">{question}</span>
        {isOpen ? <Minus className="w-5 h-5 text-zinc-400" /> : <Plus className="w-5 h-5 text-zinc-400" />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <p className="pb-6 text-zinc-500 leading-relaxed">{answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- Main Page ---

export const LandingPage = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end end"] });
  const heroOpacity = useTransform(scrollYProgress, [0, 0.1], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 0.1], [1, 0.95]);

  return (
    <div ref={containerRef} className="min-h-screen bg-white text-zinc-900 font-sans selection:bg-zinc-900 selection:text-white">
      
      {/* 1. Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold font-display tracking-tight text-zinc-900">Pulse AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-500">
            <a href="#mission" className="hover:text-zinc-900 transition-colors">Mission</a>
            <a href="#solutions" className="hover:text-zinc-900 transition-colors">Solutions</a>
            <a href="#platform" className="hover:text-zinc-900 transition-colors">Platform</a>
            <a href="#specs" className="hover:text-zinc-900 transition-colors">Specs</a>
          </div>
          <div className="flex items-center gap-4">
            {/* <Link to="/login" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors hidden sm:block">
              Log in
            </Link> */}
            <Link to="/signup">
              <Button className="rounded-full px-5 py-2 h-auto text-sm bg-zinc-900 hover:bg-zinc-800 text-white shadow-lg shadow-zinc-900/10">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* 2. Hero Section */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden border-b border-zinc-100">
        <div className="max-w-7xl mx-auto text-center relative z-10">
          <motion.div style={{ opacity: heroOpacity, scale: heroScale }}>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-100 text-xs font-medium text-emerald-700 mb-8"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Accepting Early Access Partners
            </motion.div>

            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              className="text-5xl md:text-8xl font-display font-bold tracking-tighter leading-[1.1] mb-6 text-zinc-900"
            >
              Detect health anomalies <br />
              <span className="text-[#4988C4]">before they become crises.</span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed mb-10"
            >
              Pulse AI learns your personal biological baseline to detect physiological drift. 
              Continuous, privacy-first surveillance for the proactive age.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
            >
              <Link to="/dashboard">
                <Button className="h-12 px-8 rounded-full bg-zinc-900 text-white hover:bg-zinc-800 shadow-xl shadow-zinc-900/20 flex items-center gap-2">
                  View Dashboard Demo <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="outline" className="h-12 px-8 rounded-full border-zinc-200 hover:bg-zinc-50 text-zinc-600">
                  How It Works
                </Button>
              </a>
            </motion.div>
          </motion.div>

          {/* Dashboard Preview Mockup */}
          <motion.div
            initial={{ opacity: 0, y: 60, rotateX: 20 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
            className="relative max-w-5xl mx-auto perspective-1000 group"
          >
            <div className="relative bg-white rounded-xl shadow-2xl border border-zinc-200 overflow-hidden aspect-[16/10] md:aspect-[2/1] transition-transform duration-700 group-hover:scale-[1.01]">
              {/* Mock UI Header */}
              <div className="h-10 border-b border-zinc-100 bg-zinc-50/80 flex items-center px-4 gap-2 justify-between">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400/20 border border-red-400/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400/20 border border-amber-400/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400/20 border border-emerald-400/50" />
                </div>
                <div className="text-[10px] font-mono text-zinc-400 flex items-center gap-2">
                    <Shield className="w-3 h-3" />
                    SECURE_ENCLAVE_ACTIVE
                </div>
              </div>
              
              {/* Mock UI Body */}
              <div className="flex h-full">
                {/* Sidebar */}
                <div className="w-48 hidden md:flex flex-col gap-1 border-r border-zinc-100 bg-zinc-50/30 p-3">
                    <div className="flex items-center gap-2 px-2 py-2 mb-4">
                        <div className="w-6 h-6 bg-zinc-900 rounded-md flex items-center justify-center">
                            <Activity className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-xs font-bold text-zinc-900">Pulse AI</span>
                    </div>
                    {[
                        { icon: LayoutDashboard, label: "Overview", active: true },
                        { icon: LineChart, label: "Analytics", active: false },
                        { icon: Activity, label: "Vitals", active: false },
                        { icon: FileText, label: "Reports", active: false },
                    ].map((item, i) => (
                        <div key={i} className={cn(
                            "flex items-center gap-2 px-2 py-1.5 rounded-md text-xs font-medium",
                            item.active ? "bg-white shadow-sm text-zinc-900" : "text-zinc-500"
                        )}>
                            <item.icon className="w-3.5 h-3.5" />
                            {item.label}
                        </div>
                    ))}
                </div>
                
                {/* Main Content */}
                <div className="flex-1 p-6 bg-white flex flex-col gap-6">
                    {/* Top Bar */}
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-bold text-zinc-900">Patient Monitoring</h3>
                            <p className="text-xs text-zinc-500">Live Stream • 50Hz Sampling</p>
                        </div>
                        <div className="flex gap-2">
                            <div className="px-2 py-1 bg-emerald-50 border border-emerald-100 rounded text-[10px] font-bold text-emerald-600 flex items-center gap-1">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                LIVE
                            </div>
                        </div>
                    </div>

                    {/* Main Chart Area */}
                    <div className="flex-1 bg-zinc-50/50 rounded-lg border border-zinc-100 relative overflow-hidden group/chart">
                        {/* Grid Lines */}
                        <div className="absolute inset-0 grid-pattern opacity-50" />
                        
                        {/* Chart Path (SVG) */}
                        <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                            <path d="M0,100 C20,90 40,95 60,85 C80,75 100,80 120,70 C140,60 160,65 180,55 C200,45 220,50 240,40 C260,30 280,35 300,45 C320,55 340,50 360,60 C380,70 400,65 420,75 C440,85 460,80 480,90 C500,100 520,95 540,85 C560,75 580,80 600,70 L600,200 L0,200 Z" 
                                  className="fill-zinc-900/5 stroke-none" />
                            <path d="M0,100 C20,90 40,95 60,85 C80,75 100,80 120,70 C140,60 160,65 180,55 C200,45 220,50 240,40 C260,30 280,35 300,45 C320,55 340,50 360,60 C380,70 400,65 420,75 C440,85 460,80 480,90 C500,100 520,95 540,85 C560,75 580,80 600,70" 
                                  className="stroke-zinc-900 fill-none stroke-[2]" vectorEffect="non-scaling-stroke" />
                        </svg>

                        {/* Scanning Line Animation */}
                        <div className="absolute top-0 bottom-0 w-px bg-zinc-900/20 shadow-[0_0_10px_rgba(0,0,0,0.1)] animate-[scan_3s_linear_infinite]" 
                             style={{ animation: 'scan 3s linear infinite' }} />
                        <style>{`
                            @keyframes scan {
                                0% { left: 0%; }
                                100% { left: 100%; }
                            }
                        `}</style>
                        
                        {/* Drift Alert Badge */}
                        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur border border-red-100 shadow-sm px-3 py-1.5 rounded-md flex items-center gap-2">
                            <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                            <span className="text-xs font-bold text-red-600">Drift Detected (+12%)</span>
                        </div>
                    </div>

                    {/* Metric Cards */}
                    <div className="grid grid-cols-3 gap-4 h-20">
                        {[
                            { label: "CareScore", value: "82", unit: "/100", color: "text-zinc-900" },
                            { label: "Heart Rate", value: "64", unit: "bpm", color: "text-zinc-500" },
                            { label: "HRV", value: "45", unit: "ms", color: "text-zinc-500" },
                        ].map((m, i) => (
                            <div key={i} className="bg-zinc-50 border border-zinc-100 rounded-lg p-3 flex flex-col justify-center">
                                <span className="text-[10px] uppercase tracking-wider text-zinc-400 font-semibold">{m.label}</span>
                                <div className="flex items-baseline gap-1">
                                    <span className={cn("text-xl font-bold tracking-tight", m.color)}>{m.value}</span>
                                    <span className="text-[10px] text-zinc-400">{m.unit}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
              </div>
            </div>
            
            {/* Ambient Glow */}
            <div className="absolute -inset-10 bg-gradient-to-t from-zinc-200/50 via-zinc-100/0 to-transparent blur-3xl -z-10" />
          </motion.div>
        </div>
      </section>

      {/* 3. Social Proof Ticker */}
      <section className="py-10 border-b border-zinc-100 bg-zinc-50/50">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Trusted by industry leaders</span>
            <div className="flex gap-8 md:gap-16 opacity-40 grayscale hover:grayscale-0 transition-all duration-500 items-center">
                 {/* Generic Logos */}
                 {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="flex items-center gap-2 group cursor-default">
                        <div className="w-6 h-6 bg-zinc-800 rounded-md group-hover:bg-zinc-900 transition-colors" />
                        <div className="h-2.5 w-20 bg-zinc-300 rounded-sm group-hover:bg-zinc-800 transition-colors" />
                    </div>
                 ))}
            </div>
        </div>
      </section>

      {/* 4. Problem Section */}
      <section id="mission" className="py-24 bg-white border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <FadeIn>
              <SectionBadge>The Problem</SectionBadge>
              <h2 className="text-3xl md:text-4xl font-display font-bold tracking-tight mb-6 text-zinc-900">
                Healthcare is reactive.<br />
                <span className="text-zinc-400">By the time you feel sick, it's late.</span>
              </h2>
              <p className="text-lg text-zinc-600 leading-relaxed mb-8">
                Traditional medicine relies on lagging indicators—symptoms. This "wait and see" approach misses the critical window for early intervention.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-zinc-50 rounded-xl border border-zinc-100">
                    <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0" />
                    <div>
                        <h4 className="font-bold text-zinc-900 text-sm">The "Lag" Gap</h4>
                        <p className="text-sm text-zinc-500 mt-1">
                            80% of chronic conditions show physiological markers 14-21 days before symptoms appear. Standard care misses this window completely.
                        </p>
                    </div>
                </div>
              </div>
            </FadeIn>

            <FadeIn delay={0.2} className="relative">
               <div className="absolute inset-0 bg-gradient-to-tr from-zinc-200/50 to-transparent rounded-3xl transform rotate-3" />
               <div className="relative bg-white p-8 rounded-3xl border border-zinc-200 shadow-xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                        <Activity className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                        <h4 className="font-bold text-zinc-900">The Pulse AI Approach</h4>
                        <p className="text-xs text-zinc-500">Continuous Clinical Surveillance</p>
                    </div>
                  </div>
                  
                  <div className="space-y-6">
                    <div className="flex items-center gap-4">
                        <div className="w-full bg-zinc-100 h-2 rounded-full overflow-hidden">
                            <div className="w-[15%] h-full bg-emerald-500" />
                        </div>
                        <span className="text-xs font-mono text-zinc-400 whitespace-nowrap">Day 1: Baseline</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-full bg-zinc-100 h-2 rounded-full overflow-hidden">
                            <div className="w-[35%] h-full bg-emerald-500" />
                        </div>
                        <span className="text-xs font-mono text-zinc-400 whitespace-nowrap">Day 14: Drift</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-full bg-zinc-100 h-2 rounded-full overflow-hidden relative">
                            <div className="w-[65%] h-full bg-amber-500" />
                            <div className="absolute left-[65%] -top-1 w-4 h-4 bg-white border-2 border-amber-500 rounded-full" />
                        </div>
                        <span className="text-xs font-bold text-amber-600 whitespace-nowrap">Day 21: Alert</span>
                    </div>
                  </div>
                  
                  <p className="mt-8 text-sm text-zinc-500 italic border-l-2 border-zinc-200 pl-4">
                    "Pulse AI detected the deviation 12 days before I felt the first symptom."
                  </p>
               </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 5. Use Cases */}
      <section id="solutions" className="py-24 bg-zinc-50 border-b border-zinc-100">
        <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-2xl mx-auto mb-16">
                <SectionBadge>Use Cases</SectionBadge>
                <h2 className="text-3xl md:text-4xl font-display font-bold tracking-tight text-zinc-900">
                    Precision monitoring for every need.
                </h2>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
                <FadeIn className="bg-white p-8 rounded-2xl border border-zinc-200 hover:border-zinc-300 transition-all shadow-sm">
                    <div className="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center mb-6">
                        <HeartPulse className="w-6 h-6 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-bold text-zinc-900 mb-3">Chronic Care</h3>
                    <p className="text-sm text-zinc-500 leading-relaxed">
                        For patients managing hypertension, diabetes, or autoimmune conditions. Detect flare-ups before they require hospitalization.
                    </p>
                </FadeIn>

                <FadeIn delay={0.1} className="bg-white p-8 rounded-2xl border border-zinc-200 hover:border-zinc-300 transition-all shadow-sm">
                    <div className="w-12 h-12 rounded-lg bg-emerald-50 flex items-center justify-center mb-6">
                        <Stethoscope className="w-6 h-6 text-emerald-600" />
                    </div>
                    <h3 className="text-xl font-bold text-zinc-900 mb-3">Post-Operative</h3>
                    <p className="text-sm text-zinc-500 leading-relaxed">
                        Remote patient monitoring after surgery. Reduce readmission rates by tracking recovery curves and infection markers.
                    </p>
                </FadeIn>

                <FadeIn delay={0.2} className="bg-white p-8 rounded-2xl border border-zinc-200 hover:border-zinc-300 transition-all shadow-sm">
                    <div className="w-12 h-12 rounded-lg bg-violet-50 flex items-center justify-center mb-6">
                        <Zap className="w-6 h-6 text-violet-600" />
                    </div>
                    <h3 className="text-xl font-bold text-zinc-900 mb-3">Performance & Longevity</h3>
                    <p className="text-sm text-zinc-500 leading-relaxed">
                        For biohackers and athletes. Optimize training load and recovery by understanding your true physiological baseline.
                    </p>
                </FadeIn>
            </div>
        </div>
      </section>

      {/* 6. How It Works */}
      <section id="how-it-works" className="py-32 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-20">
            <SectionBadge>Workflow</SectionBadge>
            <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight mb-4 text-zinc-900">
              From data to decision.
            </h2>
            <p className="text-zinc-500 text-lg">
              Our engine processes millions of data points to find the signal in the noise.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-px bg-gradient-to-r from-zinc-200 via-zinc-300 to-zinc-200 border-t border-dashed border-zinc-300 -z-10" />

            {[
              {
                icon: Smartphone,
                step: "01",
                title: "Ingest",
                desc: "We connect to your Apple Watch, Oura Ring, or Whoop to collect raw biometric data securely."
              },
              {
                icon: Brain,
                step: "02",
                title: "Analyze",
                desc: "Our neural networks learn your unique baseline over 30 days, filtering out daily fluctuations."
              },
              {
                icon: Stethoscope,
                step: "03",
                title: "Escalate",
                desc: "When sustained drift is confirmed, we generate a clinical report for your doctor."
              }
            ].map((item, i) => (
              <FadeIn key={i} delay={i * 0.2} className="flex flex-col items-center text-center group">
                <div className="w-24 h-24 rounded-2xl bg-white border border-zinc-100 shadow-xl shadow-zinc-100 flex items-center justify-center mb-8 relative z-10 group-hover:-translate-y-2 transition-transform duration-300">
                  <item.icon className="w-8 h-8 text-zinc-900" />
                  <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-zinc-900 text-white flex items-center justify-center font-mono text-sm font-bold border-4 border-white">
                    {item.step}
                  </div>
                </div>
                <h3 className="text-xl font-bold text-zinc-900 mb-3">{item.title}</h3>
                <p className="text-zinc-500 leading-relaxed max-w-xs">{item.desc}</p>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* 7. Key Features (Dark Mode) */}
      <section id="platform" className="py-32 px-6 bg-zinc-900 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800 border border-zinc-700 text-xs font-medium text-zinc-300 mb-6 uppercase tracking-wider">
                Platform Capabilities
              </div>
              <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight mb-4">
                Clinical-grade intelligence.
              </h2>
              <p className="text-zinc-400 text-lg">
                Built for accuracy, explainability, and speed.
              </p>
            </div>
            <Link to="/signup">
                <Button variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white">
                    Start Free Trial <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Feature 1: CareScore */}
            <FadeIn className="md:col-span-2 p-8 rounded-3xl bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800 transition-colors relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
                <Activity className="w-48 h-48 text-emerald-500" />
              </div>
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-6">
                    <Activity className="w-6 h-6 text-emerald-500" />
                </div>
                <h3 className="text-2xl font-bold mb-3">CareScore™ Technology</h3>
                <p className="text-zinc-400 max-w-md mb-8">
                    A proprietary composite score (0-100) that synthesizes severity, persistence, and cross-signal validation into a single actionable metric.
                </p>
                <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700">
                    <span className="text-2xl font-mono font-bold text-white">92</span>
                    <span className="text-xs text-zinc-500 uppercase tracking-wider">Stable Status</span>
                </div>
              </div>
            </FadeIn>

            {/* Feature 2: Drift Detection */}
            <FadeIn delay={0.1} className="p-8 rounded-3xl bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800 transition-colors">
                <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-6">
                    <LineChart className="w-6 h-6 text-blue-500" />
                </div>
                <h3 className="text-xl font-bold mb-3">Drift Detection</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                    Identifies slow-moving trends that single-point diagnostics miss. We spot the 1% daily decline that adds up.
                </p>
            </FadeIn>

            {/* Feature 3: Explainable AI */}
            <FadeIn delay={0.2} className="p-8 rounded-3xl bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800 transition-colors">
                <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-6">
                    <Brain className="w-6 h-6 text-violet-500" />
                </div>
                <h3 className="text-xl font-bold mb-3">Explainable AI</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                    No black boxes. We tell you exactly <em>why</em> your score changed (e.g., "HRV dropped 15% over 3 days").
                </p>
            </FadeIn>

            {/* Feature 4: Smart Escalation */}
            <FadeIn delay={0.3} className="md:col-span-2 p-8 rounded-3xl bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800 transition-colors flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-bold mb-2">Smart Doctor Escalation</h3>
                    <p className="text-zinc-400 text-sm max-w-md">
                        Automated recommendations for professional consultation when risk thresholds are breached.
                    </p>
                </div>
                <div className="hidden sm:flex h-12 w-12 rounded-full bg-red-500/10 border border-red-500/20 items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-red-500" />
                </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 8. Technical Specs */}
      {/* <section id="specs" className="py-24 px-6 bg-white border-b border-zinc-100">
        <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8">
                <div className="col-span-1">
                    <h3 className="text-lg font-bold text-zinc-900 mb-2">Technical Specifications</h3>
                    <p className="text-sm text-zinc-500">System architecture and data handling standards.</p>
                </div>
                <div className="col-span-3 grid grid-cols-2 md:grid-cols-3 gap-8">
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">DATA ENCRYPTION</div>
                        <div className="font-bold text-zinc-900">AES-256 + TLS 1.3</div>
                    </div>
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">SAMPLING RATE</div>
                        <div className="font-bold text-zinc-900">Up to 50Hz</div>
                    </div>
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">COMPLIANCE</div>
                        <div className="font-bold text-zinc-900">HIPAA / GDPR</div>
                    </div>
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">INTEGRATIONS</div>
                        <div className="font-bold text-zinc-900">HealthKit, Google Fit</div>
                    </div>
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">LATENCY</div>
                        <div className="font-bold text-zinc-900">&lt; 100ms Inference</div>
                    </div>
                    <div>
                        <div className="text-xs font-mono text-zinc-400 mb-1">MODEL TYPE</div>
                        <div className="font-bold text-zinc-900">LSTM / Transformer</div>
                    </div>
                </div>
            </div>
        </div>
      </section> */}

      {/* 9. FAQ Section */}
      <section className="py-24 px-6 bg-zinc-50">
        <div className="max-w-3xl mx-auto">
            <div className="text-center mb-16">
                <h2 className="text-3xl font-display font-bold text-zinc-900">Frequently Asked Questions</h2>
            </div>
            <div className="bg-white rounded-2xl border border-zinc-200 p-8 shadow-sm">
                <AccordionItem 
                    question="Does Pulse AI diagnose medical conditions?" 
                    answer="No. Pulse AI is a clinical decision support tool. We detect physiological deviations (drift) and recommend consultation. We do not provide definitive medical diagnoses."
                />
                <AccordionItem 
                    question="Is my health data secure?" 
                    answer="Absolutely. We use end-to-end encryption and process sensitive biometric data in secure enclaves. We are fully HIPAA compliant and never sell data to third parties."
                />
                <AccordionItem 
                    question="Which devices are supported?" 
                    answer="We currently support Apple Watch (Series 4+), Oura Ring (Gen 2+), Whoop, and select Garmin devices via Apple Health and Google Fit integrations."
                />
                <AccordionItem 
                    question="How long does it take to establish a baseline?" 
                    answer="The system begins providing insights after 3 days, but full baseline accuracy is achieved after 14 days of continuous wear."
                />
            </div>
        </div>
      </section>

      {/* 10. Trust & Safety */}
      <section id="trust" className="py-24 px-6 bg-white border-b border-zinc-100">
        <div className="max-w-4xl mx-auto text-center">
          <FadeIn>
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-50 shadow-sm mb-8">
              <Shield className="w-8 h-8 text-zinc-900" />
            </div>
            <h2 className="text-3xl font-display font-bold tracking-tight mb-6 text-zinc-900">
              Built on trust, not just algorithms.
            </h2>
            <p className="text-lg text-zinc-600 mb-12 max-w-2xl mx-auto">
              Pulse AI is a decision support tool, not a doctor. We prioritize human-in-the-loop verification
              and strict data privacy.
            </p>
          </FadeIn>

          <div className="grid md:grid-cols-2 gap-6 text-left">
            <FadeIn delay={0.1} className="bg-zinc-50 p-8 rounded-xl border border-zinc-200 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <Lock className="w-5 h-5 text-zinc-400" />
                <h3 className="font-bold text-zinc-900">Privacy First Architecture</h3>
              </div>
              <p className="text-zinc-500 text-sm leading-relaxed">
                Your health data is processed in a secure enclave. We utilize on-device processing where possible and never sell biometric data to advertisers.
              </p>
            </FadeIn>
            <FadeIn delay={0.2} className="bg-zinc-50 p-8 rounded-xl border border-zinc-200 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle2 className="w-5 h-5 text-zinc-400" />
                <h3 className="font-bold text-zinc-900">No Diagnosis</h3>
              </div>
              <p className="text-zinc-500 text-sm leading-relaxed">
                We detect change, not disease. All high-risk alerts are framed as "recommendations for consultation" to ensure clinical safety.
              </p>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* 11. Final CTA */}
      <section className="py-32 px-6 bg-zinc-900 text-white text-center">
        <FadeIn>
          <h2 className="text-4xl md:text-6xl font-display font-bold tracking-tighter mb-8 text-white">
            Ready to define your baseline?
          </h2>
          <p className="text-xl text-zinc-400 mb-10 max-w-xl mx-auto">
            Join thousands of users who have switched from reactive to proactive health monitoring.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup">
              <Button className="h-14 px-10 text-lg rounded-full bg-white text-zinc-900 hover:bg-zinc-100 shadow-xl shadow-white/10">
                Start Clinical Trial
              </Button>
            </Link>
            <Link to="/dashboard">
                <Button variant="outline" className="h-14 px-10 text-lg rounded-full border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white gap-2">
                    <Play className="w-4 h-4 fill-current" /> View Demo
                </Button>
            </Link>
          </div>
        </FadeIn>
      </section>

      {/* 12. Footer */}
      <footer className="py-20 px-6 bg-zinc-50 border-t border-zinc-200">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2 md:col-span-1">
                <div className="flex items-center gap-2 mb-6">
                    <div className="w-6 h-6 bg-zinc-900 rounded flex items-center justify-center">
                        <Activity className="w-3 h-3 text-white" />
                    </div>
                    <span className="font-bold font-display tracking-tight text-zinc-900">Pulse AI</span>
                </div>
                <p className="text-sm text-zinc-500 leading-relaxed">
                    Continuous clinical surveillance for the modern era.
                </p>
            </div>
            
            <div>
                <h4 className="font-bold text-zinc-900 mb-4">Product</h4>
                <ul className="space-y-3 text-sm text-zinc-500">
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Features</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Integrations</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Pricing</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Changelog</a></li>
                </ul>
            </div>

            <div>
                <h4 className="font-bold text-zinc-900 mb-4">Company</h4>
                <ul className="space-y-3 text-sm text-zinc-500">
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">About</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Careers</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Blog</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Contact</a></li>
                </ul>
            </div>

            <div>
                <h4 className="font-bold text-zinc-900 mb-4">Legal</h4>
                <ul className="space-y-3 text-sm text-zinc-500">
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Privacy Policy</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">Terms of Service</a></li>
                    <li><a href="#" className="hover:text-zinc-900 transition-colors">HIPAA Compliance</a></li>
                </ul>
            </div>
        </div>
        
        <div className="max-w-7xl mx-auto pt-8 border-t border-zinc-200 flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-zinc-400">
                © 2025 Pulse AI Systems Inc. All rights reserved.
            </div>
            <div className="flex gap-6">
                <Globe className="w-5 h-5 text-zinc-400 hover:text-zinc-900 cursor-pointer transition-colors" />
                <div className="w-5 h-5 text-zinc-400 hover:text-zinc-900 cursor-pointer transition-colors font-bold text-xs flex items-center justify-center border border-zinc-400 rounded-sm">X</div>
            </div>
        </div>
      </footer>
    </div>
  );
};
