import { useRef, useState } from "react"

import { Label } from "@/components/atoms/Label"
import { cn } from "@/lib/utils"

const ACCEPTED = ".xlsx,.xls"
const ACCEPTED_EXT = [".xlsx", ".xls"]

interface UploadDropzoneProps {
  onFile: (file: File) => void
  disabled?: boolean
}

function isAllowed(file: File): boolean {
  const lower = file.name.toLowerCase()
  return ACCEPTED_EXT.some((ext) => lower.endsWith(ext))
}

export function UploadDropzone({ onFile, disabled = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [hover, setHover] = useState(false)
  const [reject, setReject] = useState<string | null>(null)

  const pick = () => inputRef.current?.click()

  const accept = (file: File | null | undefined) => {
    if (!file) return
    if (!isAllowed(file)) {
      setReject(`Archivo rechazado: ${file.name} — solo .xlsx / .xls`)
      return
    }
    setReject(null)
    onFile(file)
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        disabled={disabled}
        onClick={pick}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setHover(true)
        }}
        onDragLeave={() => setHover(false)}
        onDrop={(e) => {
          e.preventDefault()
          setHover(false)
          if (disabled) return
          accept(e.dataTransfer.files?.[0])
        }}
        className={cn(
          "group relative flex h-32 w-full flex-col items-center justify-center gap-2",
          "border border-dashed border-border-strong bg-elev",
          "text-left transition-colors",
          !disabled && "hover:bg-surface focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary",
          hover && "bg-surface",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <Label className="text-foreground">arrastrar excel</Label>
        <span className="text-[0.74rem] text-muted-foreground">
          o hacer <strong>click</strong> para seleccionar — formatos: .xlsx, .xls
        </span>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => {
            accept(e.target.files?.[0])
            e.target.value = ""
          }}
        />
      </button>
      {reject && (
        <p className="text-[0.72rem] text-fail" role="alert">
          {reject}
        </p>
      )}
    </div>
  )
}
