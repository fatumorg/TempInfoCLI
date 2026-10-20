{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication rec {
  pname = "tempinfocli";
  version = "0.1.0";
  format = "pyproject";

  src = ./.;

  nativeBuildInputs = with pkgs.python3Packages; [
    setuptools
  ];

  propagatedBuildInputs = with pkgs.python3Packages; [
    rich
    psutil
  ];

  meta = with pkgs.lib; {
    description = "A live terminal temperature dashboard";
    mainProgram = "tempinfocli";
  };
}
