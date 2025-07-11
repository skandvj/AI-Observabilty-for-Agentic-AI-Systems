'use client'

import React from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { Sliders } from 'lucide-react'

// Import threshold management components
import ThresholdsTab from './thresholds/ThresholdsTab'

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="mt-1 text-sm text-gray-500">
              Configure dynamic thresholds for quality control
            </p>
          </div>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 bg-white rounded-lg shadow-sm mr-6">
            <nav className="p-4 space-y-2">
              <div className="flex items-center px-3 py-2 text-sm font-medium rounded-md bg-blue-50 text-blue-700 border-r-2 border-blue-700">
                <Sliders className="h-5 w-5 mr-3" />
                Dynamic Thresholds
              </div>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 bg-white rounded-lg shadow-sm p-6">
            <ThresholdsTab />
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
} 