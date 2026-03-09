import Link from 'next/link';
import Head from 'next/head';

export default function Custom500() {
  return (
    <>
      <Head>
        <title>500 - Server Error | Stratos AI Financial Advisor</title>
      </Head>
      <div className="min-h-screen bg-[#0b0d17] bg-grid flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-7xl font-bold text-red-400/60 mb-4">500</h1>
          <h2 className="text-2xl font-semibold text-white mb-4">Internal Server Error</h2>
          <p className="text-gray-500 mb-8">
            Something went wrong on our end. Please try again later.
          </p>
          <Link href="/dashboard">
            <button className="bg-primary/80 hover:bg-primary text-white px-6 py-3 rounded-lg transition-colors">
              Return to Dashboard
            </button>
          </Link>
        </div>
      </div>
    </>
  );
}
