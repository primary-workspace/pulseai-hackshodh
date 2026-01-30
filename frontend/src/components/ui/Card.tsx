import * as React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "../../lib/utils";

interface CardProps {
  delay?: number;
  children?: React.ReactNode;
  className?: string;
}

export const Card = ({ className, children, delay = 0 }: CardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={cn(
        "bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300",
        className
      )}
    >
      {children}
    </motion.div>
  );
};

interface CardHeaderProps {
  children?: React.ReactNode;
  className?: string;
}

export const CardHeader = ({ className, children }: CardHeaderProps) => (
  <div className={cn("mb-4", className)}>{children}</div>
);

interface CardTitleProps {
  children?: React.ReactNode;
  className?: string;
}

export const CardTitle = ({ className, children }: CardTitleProps) => (
  <h3 className={cn("text-sm font-semibold text-gray-500 uppercase tracking-wider", className)}>{children}</h3>
);

interface CardValueProps {
  children?: React.ReactNode;
  className?: string;
}

export const CardValue = ({ className, children }: CardValueProps) => (
  <div className={cn("text-3xl font-medium text-gray-900 tracking-tight", className)}>{children}</div>
);
