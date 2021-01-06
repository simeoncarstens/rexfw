{ pkgs ? import <nixpkgs> {} }:
with pkgs;
with pkgs.python36Packages;
let 
  csb = buildPythonPackage rec {
    pname = "csb";
    version = "1.2.5";
    src = fetchPypi {
      inherit pname version;
      sha256 = "5acdb655fa290b8b6f0f09faf15bdcefb1795487489c51eba4f57075b92f1a15";
      extension = "zip";
    };
    buildInputs = [ numpy matplotlib scipy_notests ];
    propagatedBuildInputs = [ scipy_notests numpy matplotlib ];
    doCheck = false;
  };

  rexfw = buildPythonPackage rec {
    pname = "rexfw";
    version = "0.1.0";
    src = pkgs.lib.cleanSource ./.;
    doCheck = false;
    installCheckPhase = ''
      cd rexfw/test && python run_tests.py
    '';
    buildInputs = [ numpy mpi4py openmpi csb ];
    propagatedBuildInputs = buildInputs;
  };

  scipy_notests = pkgs.python36Packages.scipy.overrideAttrs (old: {
    doCheck = false;
  });
in
  pkgs.mkShell {
    buildInputs = [ rexfw ];
  }
