'use client'
import { useState } from 'react'

export function PriceSubmitForm({ cardId, platform }: { cardId: string; platform: string }) {
  const [price, setPrice] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('loading')
    const token = localStorage.getItem('hutbin_token')
    if (!token) {
      setStatus('error')
      setMessage('You must be logged in to submit a price.')
      return
    }
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/prices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ cardId, price: Number(price.replace(/\D/g, '')), platform }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error)
      }
      setStatus('success')
      setMessage('Price submitted! Thank you.')
      setPrice('')
    } catch (err: unknown) {
      setStatus('error')
      setMessage(err instanceof Error ? err.message : 'Submission failed.')
    }
  }

  return (
    <section className="rounded-xl bg-dark-800 p-5">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-gray-400">
        Soumettre un prix
      </h2>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          placeholder="Ex: 850000"
          value={price}
          onChange={e => setPrice(e.target.value)}
          className="flex-1 rounded-lg border border-white/20 bg-dark-900 px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
          required
        />
        <button
          type="submit"
          disabled={status === 'loading'}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold hover:bg-brand-500 disabled:opacity-50 transition-colors"
        >
          {status === 'loading' ? 'Envoi...' : 'Soumettre'}
        </button>
      </form>
      {message && (
        <p className={`mt-2 text-xs ${status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
          {message}
        </p>
      )}
    </section>
  )
}
