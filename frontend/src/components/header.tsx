import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b px-6 py-4">
      <nav className="flex items-center justify-between">
        <Link className="text-lg font-semibold" href="/">
          MyPerks
        </Link>

        <div className="flex items-center gap-4">
          <Link href="/dashboard">Dashboard</Link>
          <SignedIn>
            <UserButton />
          </SignedIn>
          <SignedOut>
            <Link href="/sign-in">Sign in</Link>
          </SignedOut>
        </div>
      </nav>
    </header>
  );
}
