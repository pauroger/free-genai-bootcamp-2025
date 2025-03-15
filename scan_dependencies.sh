#!/bin/bash
# Repository Python Dependency Scanner
# This script scans a repository for Python dependencies and creates a single requirements.txt

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check required tools
function check_dependencies() {
  echo -e "${BOLD}Checking required tools...${NC}"
  
  # Check if pip is installed
  if ! command -v pip &> /dev/null; then
    echo "pip is not installed. Please install Python and pip."
    exit 1
  fi
  
  # Check if pipreqs is installed, install if not
  if ! command -v pipreqs &> /dev/null; then
    echo "Installing pipreqs..."
    pip install pipreqs
  fi
  
  echo -e "${GREEN}All required tools are available.${NC}"
}

# Process Python dependencies
function scan_python() {
  local repo_path=$1
  
  echo -e "\n${BOLD}${BLUE}Scanning Python dependencies...${NC}"
  
  # Check if we're in a virtual environment
  if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No active virtual environment detected.${NC}"
    echo -e "It's recommended to run this script within a virtual environment."
    echo -e "Activate your virtual environment first with: ${BOLD}source /path/to/venv/bin/activate${NC}"
    echo -e "Continue scanning without a virtual environment? (y/n)"
    read -r continue_scan
    if [[ ! "$continue_scan" =~ ^[Yy]$ ]]; then
      echo "Exiting..."
      exit 0
    fi
  else
    echo -e "${GREEN}Using virtual environment:${NC} $VIRTUAL_ENV"
  fi
  
  # Find Python files
  python_files=$(find "$repo_path" -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/env/*" -not -path "*/node_modules/*")
  
  if [ -z "$python_files" ]; then
    echo "No Python files found in the repository."
    return 1
  fi
  
  echo "Found $(echo "$python_files" | wc -l | tr -d ' ') Python files to analyze"
  
  # Create a temporary directory for processing
  temp_dir=$(mktemp -d)
  
  # Create a file with all Python files to scan
  echo "$python_files" > "$temp_dir/python_files.txt"
  
  # Run pipreqs on the entire repo
  echo "Analyzing Python imports across the repository..."
  pipreqs --force --savepath "$repo_path/requirements.txt" "$repo_path" 2>/dev/null
  
  # Check if requirements.txt was created
  if [ ! -f "$repo_path/requirements.txt" ]; then
    echo "Failed to generate requirements.txt. Trying alternate approach..."
    
    # Alternative approach: scan each file and consolidate
    echo "" > "$repo_path/requirements.txt"
    
    # Process each Python file's directory
    echo "$python_files" | while read -r file; do
      dir=$(dirname "$file")
      # Only process each directory once
      if [ ! -f "$temp_dir/$(echo "$dir" | md5sum | cut -d' ' -f1)" ]; then
        touch "$temp_dir/$(echo "$dir" | md5sum | cut -d' ' -f1)"
        echo "Processing: $dir"
        pipreqs "$dir" --force --savepath "$temp_dir/temp_req.txt" 2>/dev/null
        if [ -f "$temp_dir/temp_req.txt" ]; then
          cat "$temp_dir/temp_req.txt" >> "$repo_path/requirements.txt"
        fi
      fi
    done
  fi
  
  # Remove duplicates from requirements.txt
  if [ -f "$repo_path/requirements.txt" ]; then
    # Create a temporary file for sorting
    sort -u "$repo_path/requirements.txt" > "$temp_dir/sorted_req.txt"
    mv "$temp_dir/sorted_req.txt" "$repo_path/requirements.txt"
    
    # Clean up duplicate package versions - keep highest version for each package
    python -c "
      import re
      import sys

      reqs = {}
      with open('$repo_path/requirements.txt', 'r') as f:
          lines = f.readlines()

      for line in lines:
          line = line.strip()
          if not line:
              continue
          
          # Get package name and version
          match = re.match(r'([^=<>]+)([=<>]+)(.*)', line)
          if match:
              pkg, op, ver = match.groups()
              pkg = pkg.strip()
              ver = ver.strip()
              
              if pkg not in reqs:
                  reqs[pkg] = (op, ver)
              else:
                  # Simple version comparison for ==
                  if op == '==':
                      curr_op, curr_ver = reqs[pkg]
                      if curr_op == '==':
                          # Keep higher version
                          v1 = [int(part) for part in ver.split('.')]
                          v2 = [int(part) for part in curr_ver.split('.')]
                          
                          # Pad with zeros to equal length
                          max_len = max(len(v1), len(v2))
                          v1 += [0] * (max_len - len(v1))
                          v2 += [0] * (max_len - len(v2))
                          
                          if v1 > v2:
                              reqs[pkg] = (op, ver)
          else:
              # No version specified, just add the package
              reqs[line] = ('', '')

          # Write cleaned requirements in alphabetical order
      with open('$repo_path/requirements.txt', 'w') as f:
          for pkg, (op, ver) in sorted(reqs.items(), key=lambda x: x[0].lower()):
              if op and ver:
                  f.write(f'{pkg}{op}{ver}\n')
              else:
                  f.write(f'{pkg}\n')
    "
    
    pkg_count=$(wc -l < "$repo_path/requirements.txt")
    echo -e "${GREEN}Created consolidated Python requirements at:${NC} $repo_path/requirements.txt"
    echo -e "${YELLOW}Python dependencies:${NC} $pkg_count packages found"
    
    # Offer pip installation
    echo -e "\n${BLUE}Would you like to install the Python dependencies into your virtual environment? (y/n)${NC}"
    read -r install_deps
    if [[ "$install_deps" =~ ^[Yy]$ ]]; then
      echo -e "${BOLD}Installing Python dependencies...${NC}"
      pip install -r "$repo_path/requirements.txt"
      echo -e "${GREEN}Python dependencies installed.${NC}"
    fi
  else
    echo "Failed to generate requirements.txt."
    return 1
  fi
  
  # Clean up
  rm -rf "$temp_dir"
  return 0
}

# Main function
function main() {
  # Get repository path (current directory if not specified)
  repo_path=${1:-$(pwd)}
  
  # Display scan information
  echo -e "${BOLD}Repository Python Dependency Scanner${NC}"
  echo -e "Scanning repository: ${BOLD}$repo_path${NC}"
  
  # Check and install required tools
  check_dependencies
  
  # Scan for dependencies
  scan_python "$repo_path"
  
  if [ $? -eq 0 ]; then
    # Show top packages
    echo -e "\n${YELLOW}Top Python packages:${NC}"
    head -5 "$repo_path/requirements.txt"
    
    pkg_count=$(wc -l < "$repo_path/requirements.txt")
    if [ "$pkg_count" -gt 5 ]; then
      echo "... and $(($pkg_count - 5)) more packages"
    fi
    
    echo -e "\n${GREEN}${BOLD}Scan complete!${NC}"
    echo -e "Requirements file saved to: $repo_path/requirements.txt"
    echo -e "Use ${BOLD}pip install -r $repo_path/requirements.txt${NC} to install dependencies"
  fi
}

# Run the main function with the provided repo path or current directory
main "$1"
