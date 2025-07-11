'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface ContentLayoutProps {
  children: React.ReactNode
  filters?: React.ReactNode
  actions?: React.ReactNode
  className?: string
}

export default function ContentLayout({
  children,
  filters,
  actions,
  className
}: ContentLayoutProps) {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Filters and Actions Row */}
      {(filters || actions) && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {filters && (
              <div className="flex-1">
                {filters}
              </div>
            )}
            {actions && (
              <div className="flex-shrink-0">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      {children}
    </div>
  )
} 