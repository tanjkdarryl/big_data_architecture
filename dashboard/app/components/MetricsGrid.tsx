'use client'

import { formatNumber, formatDataSize } from '@/app/lib/utils'

interface MetricsGridProps {
  totalRecords: number
  dataSizeBytes: number
  recordsPerSecond: number
  bitcoinBlocks: number
  bitcoinTransactions: number
  solanaBlocks: number
  solanaTransactions: number
}

export default function MetricsGrid({
  totalRecords,
  dataSizeBytes,
  recordsPerSecond,
  bitcoinBlocks,
  bitcoinTransactions,
  solanaBlocks,
  solanaTransactions,
}: MetricsGridProps) {
  const formatRate = (rate: number) => {
    return `${rate.toFixed(2)} records/sec`
  }

  const metrics = [
    {
      label: 'Total Records',
      value: formatNumber(totalRecords),
      color: 'text-primary',
    },
    {
      label: 'Data Size',
      value: formatDataSize(dataSizeBytes),
      color: 'text-primary',
    },
    {
      label: 'Ingestion Rate',
      value: formatRate(recordsPerSecond),
      color: 'text-indigo-600',
    },
    {
      label: 'Bitcoin Blocks',
      value: formatNumber(bitcoinBlocks),
      color: 'text-bitcoin',
    },
    {
      label: 'Bitcoin Transactions',
      value: formatNumber(bitcoinTransactions),
      color: 'text-bitcoin-light',
    },
    {
      label: 'Solana Blocks',
      value: formatNumber(solanaBlocks),
      color: 'text-solana-green',
    },
    {
      label: 'Solana Transactions',
      value: formatNumber(solanaTransactions),
      color: 'text-solana-purple',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="bg-white rounded-lg shadow p-4 border border-gray-200"
        >
          <div className="text-sm text-gray-500 mb-1">{metric.label}</div>
          <div className={`text-2xl font-bold ${metric.color}`}>
            {metric.value}
          </div>
        </div>
      ))}
    </div>
  )
}
