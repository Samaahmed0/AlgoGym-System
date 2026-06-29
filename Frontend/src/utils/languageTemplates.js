export const getTemplate = (languageId) => {
  const T = {

    // ── C (all versions: GCC 7/8/9/14, Clang 7/18/19) ──────────────────────
    48: 'C_GCC', 49: 'C_GCC', 50: 'C_GCC', 103: 'C_GCC',   // GCC versions
    75: 'C_GCC', 104: 'C_GCC', 110: 'C_GCC',                 // Clang versions

    // ── C++ (all versions: GCC 7/8/9/14, Clang 7) ──────────────────────────
    52: 'CPP', 53: 'CPP', 54: 'CPP', 105: 'CPP', 76: 'CPP',

    // ── Python (2.7, 3.8, 3.11, 3.12, 3.13, 3.14) ──────────────────────────
    70: 'PYTHON2',
    71: 'PYTHON3', 92: 'PYTHON3', 100: 'PYTHON3',
    109: 'PYTHON3', 113: 'PYTHON3',

    // ── Java (OpenJDK 13, JDK 17, JavaFX 17) ───────────────────────────────
    62: 'JAVA', 91: 'JAVA', 96: 'JAVA',

    // ── JavaScript (Node.js 12, 18, 20, 22) ────────────────────────────────
    63: 'JS', 93: 'JS', 97: 'JS', 102: 'JS',

    // ── TypeScript (3.7, 5.0, 5.6) ─────────────────────────────────────────
    74: 'TS', 94: 'TS', 101: 'TS',

    // ── C# ──────────────────────────────────────────────────────────────────
    51: 'CSHARP',

    // ── Go (1.13, 1.18, 1.22, 1.23) ────────────────────────────────────────
    60: 'GO', 95: 'GO', 106: 'GO', 107: 'GO',

    // ── Rust (1.40, 1.85) ───────────────────────────────────────────────────
    73: 'RUST', 108: 'RUST',

    // ── Kotlin (1.3, 2.1) ───────────────────────────────────────────────────
    78: 'KOTLIN', 111: 'KOTLIN',

    // ── Ruby ────────────────────────────────────────────────────────────────
    72: 'RUBY',

    // ── PHP (7.4, 8.3) ──────────────────────────────────────────────────────
    68: 'PHP', 98: 'PHP',

    // ── Swift ───────────────────────────────────────────────────────────────
    83: 'SWIFT',

    // ── Scala (2.13, 3.4) ───────────────────────────────────────────────────
    81: 'SCALA', 112: 'SCALA',

    // ── R (4.0, 4.4) ────────────────────────────────────────────────────────
    80: 'R', 99: 'R',

    // ── Bash ────────────────────────────────────────────────────────────────
    46: 'BASH',

    // ── Lua ─────────────────────────────────────────────────────────────────
    64: 'LUA',

    // ── Haskell ─────────────────────────────────────────────────────────────
    61: 'HASKELL',

    // ── OCaml ───────────────────────────────────────────────────────────────
    65: 'OCAML',

    // ── Perl ────────────────────────────────────────────────────────────────
    85: 'PERL',

    // ── Dart ────────────────────────────────────────────────────────────────
    90: 'DART',

    // ── Groovy ──────────────────────────────────────────────────────────────
    88: 'GROOVY',

    // ── F# ──────────────────────────────────────────────────────────────────
    87: 'FSHARP',

    // ── Visual Basic .NET ────────────────────────────────────────────────────
    84: 'VB',

    // ── Pascal ──────────────────────────────────────────────────────────────
    67: 'PASCAL',

    // ── Fortran ─────────────────────────────────────────────────────────────
    59: 'FORTRAN',

    // These are too niche/unique to template — user writes from scratch:
    // 45 Assembly, 47 Basic, 55 Common Lisp, 56 D, 57 Elixir, 58 Erlang,
    // 65 OCaml (handled above), 69 Prolog, 77 COBOL, 79 Objective-C,
    // 82 SQL, 86 Clojure, 43 Plain Text, 44 Executable, 89 Multi-file
  };

  const templates = {

    C_GCC: `#include <stdio.h>
#include <stdlib.h>

int main() {
    // Read input
    int n;
    scanf("%d", &n);

    // Write your solution here

    return 0;
}`,

    CPP: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Read input
    int n;
    cin >> n;

    // Write your solution here

    return 0;
}`,

    PYTHON2: `import sys
input = sys.stdin.readline

# Read input
n = int(input())
a = map(int, input().split())

# Write your solution here
`,

    PYTHON3: `import sys
input = sys.stdin.readline

def solve():
    # Read input
    n = int(input())
    a = list(map(int, input().split()))

    # Write your solution here

solve()`,

    JAVA: `import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        // Read input
        int n = Integer.parseInt(br.readLine().trim());
        int[] a = Arrays.stream(br.readLine().trim().split(" "))
                        .mapToInt(Integer::parseInt).toArray();

        // Write your solution here
    }
}`,

    JS: `process.stdin.resume();
process.stdin.setEncoding('utf8');
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
    const lines = input.trim().split('\\n');
    let idx = 0;

    // Read input
    const n = parseInt(lines[idx++]);
    const a = lines[idx++].split(' ').map(Number);

    // Write your solution here

});`,

    TS: `process.stdin.resume();
process.stdin.setEncoding('utf8');
let input: string = '';
process.stdin.on('data', (d: string) => input += d);
process.stdin.on('end', () => {
    const lines = input.trim().split('\\n');
    let idx: number = 0;

    // Read input
    const n: number = parseInt(lines[idx++]);
    const a: number[] = lines[idx++].split(' ').map(Number);

    // Write your solution here

});`,

    CSHARP: `using System;
using System.Linq;

class Solution {
    static void Main(string[] args) {
        // Read input
        int n = int.Parse(Console.ReadLine());
        int[] a = Console.ReadLine().Split().Select(int.Parse).ToArray();

        // Write your solution here
    }
}`,

    GO: `package main

import (
    "bufio"
    "fmt"
    "os"
)

var reader = bufio.NewReader(os.Stdin)

func main() {
    // Read input
    var n int
    fmt.Fscan(reader, &n)

    // Write your solution here
}`,

    RUST: `use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines().map(|l| l.unwrap());

    // Read input
    let n: usize = lines.next().unwrap().trim().parse().unwrap();

    // Write your solution here
}`,
KOTLIN: `import java.io.BufferedReader
import java.io.InputStreamReader
import java.util.StringTokenizer

fun main() {
    val br = BufferedReader(InputStreamReader(System.\`in\`))

    // Read input
    val n = br.readLine().trim().toInt()
    val st = StringTokenizer(br.readLine())
    val a = IntArray(n) { st.nextToken().toInt() }

    // Write your solution here
}`,

    RUBY: `# Read input
n = gets.chomp.to_i
a = gets.chomp.split.map(&:to_i)

# Write your solution here
`,

    PHP: `<?php
// Read input
$n = intval(trim(fgets(STDIN)));
$a = array_map('intval', explode(' ', trim(fgets(STDIN))));

// Write your solution here
?>`,

    SWIFT: `import Foundation

// Read input
let n = Int(readLine()!)!
let a = readLine()!.split(separator: " ").map { Int($0)! }

// Write your solution here
`,

    SCALA: `import scala.io.StdIn._

object Main extends App {
    // Read input
    val n = readInt()
    val a = readLine().split(" ").map(_.toInt)

    // Write your solution here
}`,

    R: `# Read input
con <- file("stdin")
lines <- readLines(con)
n <- as.integer(lines[1])
a <- as.integer(strsplit(lines[2], " ")[[1]])

# Write your solution here
`,

    BASH: `#!/bin/bash
# Read input
read n
read -a a

# Write your solution here
`,

    LUA: `-- Read input
local n = tonumber(io.read())
local a = {}
for x in io.read():gmatch("%d+") do
    table.insert(a, tonumber(x))
end

-- Write your solution here
`,

    HASKELL: `import Control.Monad (replicateM)

main :: IO ()
main = do
    -- Read input
    n <- readLn :: IO Int
    a <- map read . words <$> getLine :: IO [Int]

    -- Write your solution here
`,

    OCAML: `let () =
    (* Read input *)
    let n = Scanf.scanf " %d" (fun x -> x) in
    let a = Array.init n (fun _ -> Scanf.scanf " %d" (fun x -> x)) in

    (* Write your solution here *)
    ignore (n, a)
`,

    PERL: `use strict;
use warnings;

# Read input
my $n = <STDIN>; chomp $n;
my @a = split(' ', <STDIN>);

# Write your solution here
`,

    DART: `import 'dart:io';

void main() {
    // Read input
    final n = int.parse(stdin.readLineSync()!);
    final a = stdin.readLineSync()!.split(' ').map(int.parse).toList();

    // Write your solution here
}`,

    GROOVY: `import java.util.Scanner

def sc = new Scanner(System.in)

// Read input
def n = sc.nextInt()
def a = (1..n).collect { sc.nextInt() }

// Write your solution here
`,

    FSHARP: `open System

[<EntryPoint>]
let main _ =
    // Read input
    let n = Console.ReadLine() |> int
    let a = Console.ReadLine().Split(' ') |> Array.map int

    // Write your solution here
    0`,

    VB: `Imports System

Module Solution
    Sub Main()
        ' Read input
        Dim n As Integer = Convert.ToInt32(Console.ReadLine())
        Dim a() As Integer = Array.ConvertAll(Console.ReadLine().Split(" "), AddressOf Integer.Parse)

        ' Write your solution here
    End Sub
End Module`,

    PASCAL: `program Solution;
var
    n, i: Integer;
    a: array[1..100] of Integer;
begin
    { Read input }
    Read(n);
    for i := 1 to n do
        Read(a[i]);

    { Write your solution here }
end.`,

    FORTRAN: `program solution
    implicit none
    integer :: n
    integer, allocatable :: a(:)

    ! Read input
    read(*,*) n
    allocate(a(n))
    read(*,*) a

    ! Write your solution here

end program solution`,
  };

  const key = T[languageId];
  return key ? templates[key] : '// Write your solution here\n';
};