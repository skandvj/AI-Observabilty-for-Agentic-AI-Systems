'use client'

import React from 'react'
import { ChevronRight, Plus, Download, RefreshCw, Settings, Filter, Search } from 'lucide-react'

interface Breadcrumb {
  label: string
  href?: string
}

interface PageAction {
  label: string
  icon?: React.ComponentType<any>
  variant?: 'primary' | 'secondary' | 'outline'
  onClick?: () => void
  disabled?: boolean
}

interface PageHeaderProps {
  title: string
  description?: string
  breadcrumbs?: Breadcrumb[]
  actions?: PageAction[]
  children?: React.ReactNode
  stats?: Array<{
    label: string
    value: string | number
    trend?: number
    color?: 'green' | 'red' | 'blue' | 'gray'
  }>
}

export default function PageHeader({
  title,
  description,
  breadcrumbs = [],
  actions = [],
  children,
  stats = []
}: PageHeaderProps) {
  const getButtonClasses = (variant: string = 'secondary') => {
    const base = "inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
    
    switch (variant) {
      case 'primary':
        return `${base} bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50`
      case 'outline':
        return `${base} border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50`
      default:
        return `${base} bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50`
    }
  }

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="px-4 sm:px-6 lg:px-8">
        {/* Breadcrumbs */}
        {breadcrumbs.length > 0 && (
          <nav className="flex pt-4 pb-2" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2">
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className="flex items-center">
                  {index > 0 && <ChevronRight className="h-4 w-4 text-gray-400 mx-2" />}
                  {crumb.href ? (
                    <a
                      href={crumb.href}
                      className="text-sm font-medium text-gray-500 hover:text-gray-700"
                    >
                      {crumb.label}
                    </a>
                  ) : (
                    <span className="text-sm font-medium text-gray-900">{crumb.label}</span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}

        {/* Main Header */}
        <div className="py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            {/* Title and Description */}
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate">
                {title}
              </h1>
              {description && (
                <p className="mt-1 text-sm text-gray-500">{description}</p>
              )}
            </div>

            {/* Actions */}
            {actions.length > 0 && (
              <div className="mt-4 sm:mt-0 sm:ml-4">
                <div className="flex space-x-3">
                  {actions.map((action, index) => (
                    <button
                      key={index}
                      onClick={action.onClick}
                      disabled={action.disabled}
                      className={getButtonClasses(action.variant)}
                    >
                      {action.icon && <action.icon className="h-4 w-4 mr-2" />}
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Stats */}
          {stats.length > 0 && (
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map((stat, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        {stat.label}
                      </p>
                      <p className="text-lg font-semibold text-gray-900">
                        {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                      </p>
                    </div>
                    {stat.trend !== undefined && (
                      <div className={`text-xs font-medium ${
                        stat.trend > 0 ? 'text-green-600' : 
                        stat.trend < 0 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {stat.trend > 0 ? '+' : ''}{stat.trend}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Custom Children */}
          {children && (
            <div className="mt-4">
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 