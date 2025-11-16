"use client";

import { AuroraText } from "@/components/aurora-text";
import { Icons } from "@/components/icons";
import { Section } from "@/components/section";
import { buttonVariants } from "@/components/ui/genericButton";
import { siteConfig } from "@/lib/config";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import Link from "next/link";
import { lazy, Suspense, useEffect, useState } from "react";

const ease = [0.16, 1, 0.3, 1];

const LazySpline = lazy(() => import("@splinetool/react-spline"));

// Desktop version - COMPACT SPACING
function DesktopHero({ showSpline }: { showSpline: boolean }) {
  return (
    <div className="relative w-full">
      <div className="relative grid grid-cols-2 gap-x-8 w-full p-12 border-x">
        <div className="flex flex-col justify-start items-start col-span-1">
          <div className="flex w-full max-w-3xl flex-col overflow-hidden pt-2">
            <motion.h1
              className="text-left text-4xl font-semibold leading-tight text-foreground sm:text-5xl md:text-6xl tracking-tighter"
              initial={{ filter: "blur(10px)", opacity: 0, y: 50 }}
              animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
              transition={{
                duration: 1,
                ease,
                staggerChildren: 0.2,
              }}
            >
              <motion.span
                className="inline-block text-balance"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.8,
                  delay: 0.5,
                  ease,
                }}
              >
                <AuroraText className="leading-tight font-bold">
                  {siteConfig.hero.title}
                </AuroraText>{" "}
              </motion.span>
            </motion.h1>
            <motion.p
              className="text-left max-w-xl leading-normal text-muted-foreground sm:text-lg sm:leading-normal text-balance mt-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.6,
                duration: 0.8,
                ease,
              }}
            >
              {siteConfig.hero.description}
            </motion.p>
          </div>

          <div className="relative mt-3">
            <motion.div
              className="flex w-full max-w-2xl flex-col items-start justify-start space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.8, ease }}
            >
              <Link
                href="/login"
                className={cn(
                  buttonVariants({ variant: "default" }),
                  "w-full sm:w-auto text-background flex gap-2 rounded-lg"
                )}
              >
                <Icons.logo className="h-6 w-6" />
                {siteConfig.hero.cta}
              </Link>
            </motion.div>
            <motion.p
              className="mt-2 text-sm text-muted-foreground text-left"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.0, duration: 0.8 }}
            >
              {siteConfig.hero.ctaDescription}
            </motion.p>
          </div>
        </div>
      </div>

      <div className="absolute top-0 right-0 w-1/2 h-full pointer-events-none overflow-hidden">
        <Suspense>
          {showSpline && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 1 }}
              className="w-full h-full flex items-center justify-center"
            >
              <LazySpline
                scene="https://prod.spline.design/mZBrYNcnoESGlTUG/scene.splinecode"
                className="absolute inset-0 w-full h-full origin-top-left flex items-center justify-center"
              />
            </motion.div>
          )}
        </Suspense>
      </div>
    </div>
  );
}

// Mobile version - COMPACT SPACING
function MobileHero() {
  return (
    <div className="relative w-full h-[calc(46.1vh-var(--header-height))] overflow-hidden">
      <div className="flex flex-col items-center justify-center w-full h-full p-6 border-x gap-2">
        <div className="flex flex-col items-center justify-center w-full max-w-2xl">
          <div className="flex w-full flex-col overflow-hidden pt-2">
            <motion.h1
              className="text-center text-3xl font-semibold leading-tight text-foreground sm:text-4xl tracking-tighter"
              initial={{ filter: "blur(10px)", opacity: 0, y: 50 }}
              animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
              transition={{
                duration: 1,
                ease,
                staggerChildren: 0.2,
              }}
            >
              <motion.span
                className="inline-block text-balance"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.8,
                  delay: 0.5,
                  ease,
                }}
              >
                <AuroraText className="leading-tight font-bold">
                  {siteConfig.hero.title}
                </AuroraText>{" "}
              </motion.span>
            </motion.h1>
            <motion.p
              className="text-center max-w-xl mx-auto leading-normal text-muted-foreground text-base sm:leading-normal text-balance mt-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.6,
                duration: 0.8,
                ease,
              }}
            >
              {siteConfig.hero.description}
            </motion.p>
          </div>

          <motion.div
            className="relative mt-3 w-full flex flex-col items-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.8, ease }}
          >
            <Link
              href="/login"
              className={cn(
                buttonVariants({ variant: "default" }),
                "w-full sm:w-auto text-background flex gap-2 rounded-lg"
              )}
            >
              <Icons.logo className="h-6 w-6" />
              {siteConfig.hero.cta}
            </Link>
            <motion.p
              className="mt-2 text-sm text-muted-foreground text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.0, duration: 0.8 }}
            >
              {siteConfig.hero.ctaDescription}
            </motion.p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export function Hero() {
  const [showSpline, setShowSpline] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  useEffect(() => {
    if (!isMobile) {
      const timer = setTimeout(() => {
        setShowSpline(true);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isMobile]);

  return (
    <Section id="hero">
      {isMobile ? <MobileHero /> : <DesktopHero showSpline={showSpline} />}
    </Section>
  );
}
