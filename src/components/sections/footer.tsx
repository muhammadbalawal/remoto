import { Icons } from "@/components/icons";
import { BorderText } from "@/components/ui/border-number";
import { siteConfig } from "@/lib/config";

export function Footer() {
  return (
    <footer className="flex flex-col gap-y-5 rounded-lg p-5  container max-w-[var(--container-max-width)] mx-auto">
      <BorderText
        text={siteConfig.footer.brandText}
        className="text-[clamp(3rem,15vw,10rem)] overflow-hidden font-mono tracking-tighter font-medium"
      />
    </footer>
  );
}
