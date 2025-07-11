'use client'

import React from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import ApiTestInterface from '@/components/api/ApiTestInterface'

export default function ApiTestPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Testing</h1>
          <p className="mt-1 text-sm text-gray-500">
            Test API endpoints, submit content for analysis, and explore system responses
          </p>
        </div>

        <ApiTestInterface />
      </div>
    </DashboardLayout>
  )
} 