import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="fixed inset-0 box-border flex min-h-screen w-full items-center justify-center overflow-auto p-4">
      <div className="flex w-full justify-center">
        <SignIn
          appearance={{
            elements: {
              card: "shadow-sm border border-gray-200",
              cardBox: "mx-auto w-full",
              rootBox: "mx-auto w-full max-w-md",
            },
          }}
        />
      </div>
    </main>
  );
}
