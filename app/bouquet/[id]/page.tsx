"use client";

import React, { useEffect, useState } from "react";

export default function BouquetPage({ params }: { params: { id: string } }) {
  const [bouquet, setBouquet] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/bouquets/${params.id}`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject("Not found")))
      .then(setBouquet)
      .catch(() => setError("This link is invalid or expired."));
  }, [params.id]);

  if (error) return <p>{error}</p>;
  if (!bouquet) return <p>Loading...</p>;

  return (
    <main>
      <h1>Bouquet</h1>
      <pre>{JSON.stringify(bouquet, null, 2)}</pre>
    </main>
  );
}
