import { Link } from "react-router-dom";
import { Activity, ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";

export const AuthLayout = ({ children, title, subtitle }: { children: React.ReactNode; title: string; subtitle: string }) => {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-zinc-50">
      {/* Left Panel - Brand & Art (Desktop Only) */}
      <div className="hidden md:flex w-1/2 bg-zinc-900 text-white p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 grid-pattern opacity-10" />
        {/* Abstract Art Element */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-tr from-blue-600/20 via-violet-600/20 to-emerald-500/20 rounded-full blur-3xl animate-pulse" />
        
        <Link to="/" className="flex items-center gap-2 relative z-10 group w-fit">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center transition-transform group-hover:rotate-90 duration-500">
            <Activity className="w-5 h-5 text-zinc-900" />
          </div>
          <span className="text-xl font-bold font-display tracking-tight">Pulse AI</span>
        </Link>

        <div className="relative z-10 max-w-lg">
          <h2 className="text-5xl font-display font-bold mb-6 leading-tight">Clinical intelligence for the modern era.</h2>
          <p className="text-zinc-400 text-lg leading-relaxed">Join the network of physicians and patients defining the future of continuous surveillance.</p>
        </div>

        <div className="relative z-10 text-sm text-zinc-500 flex gap-6">
          <span>© 2025 Pulse AI Systems Inc.</span>
          <a href="#" className="hover:text-white transition-colors">Privacy</a>
          <a href="#" className="hover:text-white transition-colors">Terms</a>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex flex-col relative bg-white md:bg-zinc-50">
        {/* Mobile Header / Back Button */}
        <div className="p-6 flex justify-between items-center md:absolute md:top-8 md:right-8 md:p-0 z-20">
            <Link to="/" className="flex items-center gap-2 text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors group">
                <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
                Back to Home
            </Link>
            
            {/* Mobile Logo */}
            <Link to="/" className="md:hidden flex items-center gap-2">
                <div className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center">
                    <Activity className="w-5 h-5 text-white" />
                </div>
            </Link>
        </div>

        <div className="flex-1 flex items-center justify-center p-6 md:p-12">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="w-full max-w-md space-y-8 bg-white md:bg-transparent md:p-0 p-8 rounded-2xl md:rounded-none shadow-xl md:shadow-none border border-zinc-100 md:border-none"
          >
            <div>
              <h1 className="text-3xl md:text-4xl font-display font-bold text-zinc-900 tracking-tight">{title}</h1>
              <p className="mt-3 text-zinc-500 text-lg">{subtitle}</p>
            </div>

            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
};
