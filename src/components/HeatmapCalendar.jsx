import React from 'react'
import { format, startOfWeek, addDays, startOfYear, endOfYear, eachWeekOfInterval, isSameMonth, isSameYear } from 'date-fns'

const HeatmapCalendar = ({ data = [] }) => {
  // Create a map for quick data lookup
  const dataMap = new Map()
  data.forEach(item => {
    const dateStr = format(new Date(item.date), 'yyyy-MM-dd')
    dataMap.set(dateStr, item)
  })

  // Get the current year's date range
  const now = new Date()
  const yearStart = startOfYear(now)
  const yearEnd = endOfYear(now)
  
  // Get all weeks in the year
  const weeks = eachWeekOfInterval({ start: yearStart, end: yearEnd })
  
  // Get month labels with proper positioning
  const getMonthLabels = () => {
    const months = []
    let currentMonth = null
    let monthStartWeek = 0
    
    weeks.forEach((weekStart, weekIndex) => {
      const month = format(weekStart, 'MMM')
      if (month !== currentMonth) {
        // If this is a new month, finish the previous month
        if (currentMonth !== null) {
          // Skip the first December label (December 2024) to prevent overlap with January
          if (!(currentMonth === 'Dec' && monthStartWeek === 0)) {
            // Position slightly offset from the start for better visual balance
            months.push({
              month: currentMonth,
              weekIndex: monthStartWeek,
              position: monthStartWeek * 13 // Slightly increased from 12 for better spacing
            })
          }
        }
        
        // Start tracking the new month
        currentMonth = month
        monthStartWeek = weekIndex
      }
    })
    
    // Handle the last month
    if (currentMonth !== null) {
      // Position slightly offset from the start for better visual balance
      months.push({
        month: currentMonth,
        weekIndex: monthStartWeek,
        position: monthStartWeek * 13 // Slightly increased from 12 for better spacing
      })
    }
    
    return months
  }

  const monthLabels = getMonthLabels()

  // Get workday labels (Monday-Friday)
  const workdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

  // Get cell data for a specific day
  const getCellData = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd')
    return dataMap.get(dateStr) || { date: dateStr, count: 0, level: 0 }
  }

  // Get tooltip text
  const getTooltipText = (cellData) => {
    const date = format(new Date(cellData.date), 'MMM d, yyyy')
    if (cellData.count === 0) {
      return `No gym time on ${date}`
    }
    const hours = Math.floor(cellData.count / 60)
    const minutes = cellData.count % 60
    const timeStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
    return `${timeStr} on ${date}`
  }

  // Filter weeks to only show workdays (Monday-Friday)
  const getWorkdayCells = (weekStart) => {
    const workdayCells = []
    for (let dayIndex = 0; dayIndex < 5; dayIndex++) { // Monday to Friday
      const date = addDays(weekStart, dayIndex)
      const cellData = getCellData(date)
      const isCurrentYear = date.getFullYear() === now.getFullYear()
      const isFutureDate = date > now

      if (!isCurrentYear || isFutureDate) {
        workdayCells.push(
          <div
            key={dayIndex}
            className="heatmap-cell bg-transparent"
            title="Outside current year or future date"
          />
        )
      } else {
        workdayCells.push(
          <div
            key={dayIndex}
            className={`
              heatmap-cell cursor-pointer
              heatmap-level-${cellData.level}
              hover:ring-2 hover:ring-blue-300 hover:ring-opacity-50
            `}
            title={getTooltipText(cellData)}
            data-date={cellData.date}
            data-count={cellData.count}
          />
        )
      }
    }
    return workdayCells
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        {/* Month labels */}
        <div className="relative h-6 mb-2 ml-12 overflow-hidden">
          {monthLabels.map((monthLabel, index) => (
            <div
              key={index}
              className="absolute text-xs text-gray-600 font-medium whitespace-nowrap top-0"
              style={{ left: `${monthLabel.position}px` }}
            >
              {monthLabel.month}
            </div>
          ))}
        </div>

        <div className="flex">
          {/* Workday labels */}
          <div className="flex flex-col justify-between h-16 mr-2 text-xs text-gray-600">
            {workdayLabels.map((day, index) => (
              <div key={index} className="h-3 flex items-center font-medium">
                {day}
              </div>
            ))}
          </div>

          {/* Heatmap grid - only workdays */}
          <div className="flex space-x-0.5">
            {weeks.map((weekStart, weekIndex) => (
              <div key={weekIndex} className="flex flex-col space-y-0.5">
                {getWorkdayCells(weekStart)}
              </div>
            ))}
          </div>
        </div>

        {/* Summary stats */}
        <div className="mt-4 text-sm text-gray-600">
          <div className="flex flex-wrap gap-4">
            <span>
              Total active days: {data.filter(d => d.count > 0).length}
            </span>
            <span>
              Total gym time: {Math.floor(data.reduce((sum, d) => sum + d.count, 0) / 60)}h {data.reduce((sum, d) => sum + d.count, 0) % 60}m
            </span>
            <span>
              Best day: {Math.max(...data.map(d => d.count), 0)} minutes
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HeatmapCalendar
